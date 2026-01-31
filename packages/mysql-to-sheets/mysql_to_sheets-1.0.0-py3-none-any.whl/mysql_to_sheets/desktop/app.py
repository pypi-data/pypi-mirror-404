"""Desktop application entry point for MySQL to Google Sheets sync.

This module provides the main entry point for the PyInstaller-bundled
desktop application. It:
- Finds an available port
- Launches the Flask web dashboard
- Automatically opens the browser
- Detects first-run and shows setup wizard
- Handles graceful shutdown
- Provides system tray with status indicator
- Supports background sync operations
- Sends native desktop notifications
"""

import logging
import os
import signal
import socket
import sys
import threading
import time
import webbrowser
from typing import NoReturn

from mysql_to_sheets import __version__
from mysql_to_sheets.core.paths import (
    copy_env_example,
    ensure_directories,
    get_config_dir,
    get_data_dir,
    get_logs_dir,
    is_first_run,
)

logger = logging.getLogger(__name__)


def find_available_port(start_port: int = 5000, max_attempts: int = 100) -> int:
    """Find an available port to bind the server.

    Args:
        start_port: Port to start searching from.
        max_attempts: Maximum number of ports to try.

    Returns:
        An available port number.

    Raises:
        RuntimeError: If no available port is found.
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError(
        f"Could not find an available port in range {start_port}-{start_port + max_attempts}"
    )


def open_browser(url: str, delay: float = 1.5) -> None:
    """Open the browser after a short delay.

    Args:
        url: URL to open.
        delay: Seconds to wait before opening (allows server to start).
    """

    def _open() -> None:
        time.sleep(delay)
        webbrowser.open(url)

    thread = threading.Thread(target=_open, daemon=True)
    thread.start()


def print_startup_info(port: int, first_run: bool) -> None:
    """Print startup information to console.

    Args:
        port: The port the server is running on.
        first_run: Whether this is the first run.
    """
    print()
    print("=" * 60)
    print(f"  MySQL to Google Sheets Sync v{__version__}")
    print("=" * 60)
    print()
    print(f"  Server running at: http://127.0.0.1:{port}")
    print()
    print("  Configuration directories:")
    print(f"    Config:  {get_config_dir()}")
    print(f"    Logs:    {get_logs_dir()}")
    print(f"    Data:    {get_data_dir()}")
    print()

    if first_run:
        print("  FIRST RUN DETECTED")
        print("  ------------------")
        print("  Please complete the setup wizard in your browser.")
        print(f"  Opening: http://127.0.0.1:{port}/setup")
    else:
        print("  Opening dashboard in your browser...")

    print()
    print("  Press Ctrl+C to stop the server")
    print("=" * 60)
    print()


def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown."""

    def handle_signal(signum: int, frame: object) -> NoReturn:
        print("\n\nShutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


def start_scheduler_if_enabled() -> None:
    """Start the scheduler if enabled in configuration.

    This function starts the scheduler in the background when
    SCHEDULER_ENABLED=true is set in the configuration.
    """
    from mysql_to_sheets.core.config import get_config

    config = get_config()
    if not config.scheduler_enabled:
        return

    try:
        from mysql_to_sheets.core.scheduler import get_scheduler_service

        print("Starting scheduler...")
        service = get_scheduler_service(config)
        service.start()

        status = service.get_status()
        print(f"Scheduler started with {status['enabled_jobs']} enabled job(s)")
    except ImportError as e:
        print(f"Warning: Could not start scheduler (APScheduler not installed): {e}")
    except Exception as e:
        print(f"Warning: Failed to start scheduler: {e}")


def stop_scheduler() -> None:
    """Stop the scheduler if it's running."""
    try:
        from mysql_to_sheets.core.scheduler import get_scheduler_service

        service = get_scheduler_service()
        if service.is_running:
            print("Stopping scheduler...")
            service.stop()
    except Exception:
        pass  # Ignore errors during shutdown


def _has_active_schedules() -> bool:
    """Check if there are any enabled schedules.

    Returns:
        True if at least one enabled schedule exists.
    """
    try:
        from mysql_to_sheets.core.tenant import get_tenant_db_path
        from mysql_to_sheets.models.schedules import ScheduleRepository

        db_path = get_tenant_db_path()
        repo = ScheduleRepository(db_path)
        schedules = repo.list_all(limit=100)
        return any(s.enabled for s in schedules)
    except Exception as e:
        logger.debug(f"Could not check schedules: {e}")
        return False


def _start_heartbeat_monitor(
    app,
    notifier,
    tray,
    check_interval: float = 10.0,
    timeout: float = 20.0,
) -> None:
    """Start background thread to monitor browser heartbeat.

    When browser closes (heartbeat stops), either exit the app or
    stay in tray if schedules are running.

    Args:
        app: Flask application instance.
        notifier: Desktop notifier for showing notifications.
        tray: System tray instance.
        check_interval: Seconds between heartbeat checks.
        timeout: Seconds without heartbeat to consider browser closed.
    """

    def _monitor() -> None:
        # Wait for initial heartbeat (browser needs time to load)
        time.sleep(timeout + 5)

        while True:
            time.sleep(check_interval)

            last_heartbeat = app.config.get("LAST_HEARTBEAT", 0)
            if last_heartbeat == 0:
                # No heartbeat received yet - browser might still be loading
                continue

            age = time.time() - last_heartbeat
            if age > timeout:
                # Browser appears to be closed
                logger.info(f"Browser heartbeat timeout ({age:.1f}s > {timeout}s)")

                if _has_active_schedules():
                    # Stay running for schedules
                    logger.info("Active schedules found - staying in tray")
                    if notifier:
                        try:
                            notifier.send(
                                title="Running in Background",
                                message="Browser closed. App will continue running for scheduled syncs. Quit from the tray menu when done.",
                            )
                        except Exception as e:
                            logger.debug(f"Could not send notification: {e}")
                    # Keep monitoring in case browser reopens
                    continue
                else:
                    # No schedules - exit the app
                    logger.info("No active schedules - shutting down")
                    print("\n\nBrowser closed - shutting down...")
                    # Trigger shutdown
                    os.kill(os.getpid(), signal.SIGTERM)
                    break

    thread = threading.Thread(target=_monitor, daemon=True, name="heartbeat-monitor")
    thread.start()
    logger.debug("Heartbeat monitor started")


def setup_desktop_integration(port: int) -> tuple:
    """Set up desktop-specific integrations (tray, notifications, background sync, hotkeys).

    Args:
        port: The port the web dashboard is running on.

    Returns:
        Tuple of (tray, notifier, background_manager, status_window, hotkey_manager) or None for each if unavailable.
    """
    tray = None
    notifier = None
    bg_manager = None
    status_window = None

    try:
        from mysql_to_sheets.desktop.background import (
            BackgroundSyncManager,
            SyncProgress,
            SyncResult,
            SyncStatus,
        )
        from mysql_to_sheets.desktop.notifications import (
            DesktopNotifier,
            NotificationConfig,
        )
        from mysql_to_sheets.desktop.tray import SystemTray, TrayStatus

        # Try to initialize status window (optional - requires ttkbootstrap)
        try:
            from mysql_to_sheets.desktop.status_window import StatusWindow

            status_window = StatusWindow()
            if not status_window.is_available:
                status_window = None
        except ImportError:
            logger.debug("Status window not available (ttkbootstrap not installed)")

        # Initialize notifier
        notifier = DesktopNotifier(NotificationConfig(enabled=True))

        # Initialize background manager with notification callbacks
        def on_sync_complete(result: SyncResult) -> None:
            if notifier:
                if result.status == SyncStatus.SUCCESS:
                    notifier.sync_success(result.rows_synced, result.duration_seconds)
                elif result.status == SyncStatus.FAILED:
                    notifier.sync_failed(
                        result.error_message or "Unknown error",
                        result.error_code,
                    )

            # Update status window
            if status_window:
                if result.status == SyncStatus.SUCCESS:
                    status_window.update_status("ready")
                    status_window.update_last_sync(
                        rows=result.rows_synced,
                        duration_seconds=result.duration_seconds,
                        sync_time=result.completed_at,
                    )
                elif result.status == SyncStatus.FAILED:
                    status_window.update_status("error", result.error_message or "")

            # Update tray status with enhanced info
            if tray:
                if result.status == SyncStatus.SUCCESS:
                    tray.set_status(
                        TrayStatus.IDLE,
                        rows_synced=result.rows_synced,
                    )
                elif result.status == SyncStatus.FAILED:
                    error_info = f"{result.error_code}: {result.error_message}" if result.error_code else result.error_message
                    tray.set_status(
                        TrayStatus.ERROR,
                        error_msg=error_info,
                    )

        def on_status_change(status: SyncStatus) -> None:
            if tray:
                if status == SyncStatus.RUNNING:
                    tray.set_status(TrayStatus.SYNCING)
                elif status == SyncStatus.IDLE:
                    tray.set_status(TrayStatus.IDLE)

            # Update status window
            if status_window:
                status_map = {
                    SyncStatus.RUNNING: "syncing",
                    SyncStatus.IDLE: "ready",
                    SyncStatus.SUCCESS: "ready",
                    SyncStatus.FAILED: "error",
                }
                status_window.update_status(status_map.get(status, "ready"))

        def on_progress(progress: SyncProgress) -> None:
            """Handle progress updates from background sync."""
            if status_window:
                status_window.update_progress(
                    percent=progress.percent,
                    phase=progress.phase,
                    message=progress.message,
                )

        bg_manager = BackgroundSyncManager(
            on_sync_complete=on_sync_complete,
            on_status_change=on_status_change,
            on_progress=on_progress,
        )

        # Initialize system tray with callbacks
        def on_sync_now() -> None:
            if bg_manager:
                bg_manager.run_sync(config_name="Quick Sync")

        def on_sync_config(config_id: int) -> None:
            """Trigger sync for a specific config."""
            if bg_manager:
                bg_manager.run_sync(config_id=config_id, config_name=f"Config {config_id}")

        def on_pause_toggle() -> bool:
            if bg_manager:
                if bg_manager.is_paused:
                    bg_manager.resume()
                    if tray:
                        tray.set_status(TrayStatus.IDLE)
                    if status_window:
                        status_window.update_status("ready")
                    return False
                else:
                    bg_manager.pause()
                    if tray:
                        tray.set_status(TrayStatus.PAUSED)
                    if status_window:
                        status_window.update_status("paused")
                    return True
            return False

        def on_quit() -> None:
            print("\n\nShutting down from tray...")
            if status_window:
                status_window.destroy()
            stop_scheduler()
            sys.exit(0)

        def get_last_sync_info() -> str:
            if bg_manager:
                return bg_manager.get_last_result_summary()
            return "No syncs yet"

        def is_paused() -> bool:
            return bg_manager.is_paused if bg_manager else False

        def get_configs() -> list[dict]:
            """Get list of sync configs for tray submenu."""
            try:
                from mysql_to_sheets.models.sync_configs import SyncConfigRepository

                repo = SyncConfigRepository()
                configs = repo.list_all(limit=10)
                return [
                    {
                        "id": c.id,
                        "name": c.name,
                        "enabled": c.enabled,
                    }
                    for c in configs
                ]
            except Exception as e:
                logger.debug(f"Could not fetch configs: {e}")
                return []

        def get_schedules() -> list[dict]:
            """Get list of schedules for tray submenu."""
            try:
                from mysql_to_sheets.models.schedules import ScheduleRepository

                repo = ScheduleRepository()
                schedules = repo.list_all(limit=10)
                return [
                    {
                        "name": s.name,
                        "enabled": s.enabled,
                        "next_run": s.next_run.strftime("%H:%M") if s.next_run else "",
                    }
                    for s in schedules
                ]
            except Exception as e:
                logger.debug(f"Could not fetch schedules: {e}")
                return []

        def get_databases() -> list[dict]:
            """Get list of database integrations for tray submenu."""
            try:
                from mysql_to_sheets.models.integrations import get_integration_repository

                repo = get_integration_repository()
                integrations = repo.list_all(limit=10)
                return [
                    {
                        "id": i.id,
                        "name": i.name,
                        "integration_type": i.integration_type,
                        "health_status": i.health_status,
                    }
                    for i in integrations
                ]
            except Exception as e:
                logger.debug(f"Could not fetch databases: {e}")
                return []

        tray = SystemTray(
            port=port,
            on_sync_now=on_sync_now,
            on_sync_config=on_sync_config,
            on_pause_toggle=on_pause_toggle,
            on_quit=on_quit,
            get_last_sync_info=get_last_sync_info,
            get_configs=get_configs,
            get_schedules=get_schedules,
            get_databases=get_databases,
            is_paused=is_paused,
            status_window=status_window,
        )

        logger.info("Desktop integrations initialized")

    except ImportError as e:
        logger.warning(f"Desktop integrations not available: {e}")
    except Exception as e:
        logger.warning(f"Failed to initialize desktop integrations: {e}")

    # Initialize global hotkeys (separate try block - optional feature)
    hotkey_manager = None
    try:
        from mysql_to_sheets.desktop.hotkey_presets import get_default_bindings
        from mysql_to_sheets.desktop.hotkeys import get_hotkey_manager
        from mysql_to_sheets.desktop.settings_dialog import load_settings

        settings = load_settings()
        if settings.get("shortcuts_enabled", True):
            hotkey_manager = get_hotkey_manager()
            if hotkey_manager.is_available:
                # Register default bindings with appropriate callbacks
                for binding in get_default_bindings():
                    if not binding.enabled:
                        continue

                    callback = None
                    if binding.action.value == "trigger_sync" and bg_manager:
                        callback = lambda: bg_manager.run_sync(config_name="Hotkey Sync")
                    elif binding.action.value == "open_dashboard":
                        callback = lambda p=port: webbrowser.open(f"http://127.0.0.1:{p}/")
                    elif binding.action.value == "toggle_status_window" and status_window:
                        callback = lambda sw=status_window: sw.show() if sw else None
                    elif binding.action.value == "pause_resume" and bg_manager and tray:
                        def toggle_pause():
                            if bg_manager.is_paused:
                                bg_manager.resume()
                                tray.set_status(TrayStatus.IDLE)
                            else:
                                bg_manager.pause()
                                tray.set_status(TrayStatus.PAUSED)
                        callback = toggle_pause

                    if callback:
                        hotkey_manager.register_binding(binding, callback)

                hotkey_manager.start()
                logger.info("Global hotkeys initialized")
    except ImportError:
        logger.debug("Hotkey support not available (pynput not installed)")
    except Exception as e:
        logger.warning(f"Failed to initialize hotkeys: {e}")

    return tray, notifier, bg_manager, status_window, hotkey_manager


def main() -> None:
    """Main entry point for the desktop application.

    This function:
    1. Ensures all directories exist
    2. Copies .env.example on first run
    3. Finds an available port
    4. Initializes desktop integrations (tray, notifications)
    5. Starts the scheduler if enabled
    6. Starts the Flask server
    7. Opens the browser automatically
    """
    # Set up graceful shutdown
    setup_signal_handlers()

    # Ensure all directories exist
    ensure_directories()

    # Set database paths for Flask app
    # This ensures the web app uses the correct Application Support directory
    # instead of relative paths based on the working directory
    data_dir = get_data_dir()
    os.environ["TENANT_DB_PATH"] = str(data_dir / "tenant.db")
    os.environ["SCHEDULER_DB_PATH"] = str(data_dir / "scheduler.db")

    # Check if this is first run
    first_run = is_first_run()

    # Copy .env.example on first run
    if first_run:
        copy_env_example()

    # Find available port
    try:
        port = find_available_port()
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Print startup info
    print_startup_info(port, first_run)

    # Set up desktop integrations (tray, notifications, background sync, status window, hotkeys)
    tray, notifier, bg_manager, status_window, hotkey_manager = setup_desktop_integration(port)

    # Start system tray
    if tray and tray.is_available:
        tray.start()
        print("  System tray: Active (check menu bar/system tray)")

    # Report status window availability
    if status_window and status_window.is_available:
        print("  Status window: Available (via tray menu)")

    # Report hotkey manager status
    if hotkey_manager and hotkey_manager.is_running():
        print("  Global hotkeys: Active")

    # Start scheduler if enabled (only if not first run)
    if not first_run:
        start_scheduler_if_enabled()

    # Always open to login - the @login_required decorator handles auth
    # This ensures users see the login screen first
    url = f"http://127.0.0.1:{port}/login"

    # Import Flask app here to avoid circular imports
    from mysql_to_sheets.web.app import create_app

    app = create_app()

    # Check for native window availability
    native_window = None
    use_native_window = os.environ.get("MYSQL_TO_SHEETS_BROWSER_MODE", "").lower() != "true"

    if use_native_window:
        try:
            from mysql_to_sheets.desktop.window import DesktopWindow

            native_window = DesktopWindow(
                title="MySQL to Sheets Sync",
                url=url,
                width=1200,
                height=800,
            )
            if native_window.is_available:
                print("  Window mode: Native (pywebview)")

                # Update tray callbacks for native window
                if tray:
                    # Store original callback
                    original_open_dashboard = tray._open_dashboard

                    def open_native_window() -> None:
                        if native_window and native_window.is_running:
                            native_window.restore()
                        else:
                            # Fall back to browser
                            original_open_dashboard()

                    tray._open_dashboard = open_native_window
            else:
                native_window = None
                print("  Window mode: Browser (pywebview unavailable)")
        except ImportError:
            native_window = None
            print("  Window mode: Browser (pywebview not installed)")

    if native_window is None:
        use_native_window = False
        # Open browser after delay (allows server to start)
        open_browser(url)
        print("  Window mode: Browser")

    # Start heartbeat monitor to detect browser close (only in browser mode)
    if not use_native_window:
        _start_heartbeat_monitor(app, notifier, tray)

    # Start Flask server in a thread for native window mode
    def run_flask_server() -> None:
        app.run(
            host="127.0.0.1",
            port=port,
            debug=False,
            use_reloader=False,  # Disable reloader in bundled app
            threaded=True,
        )

    # Run the Flask server and window
    try:
        if native_window and native_window.is_available:
            # Start Flask in background thread
            flask_thread = threading.Thread(target=run_flask_server, daemon=True)
            flask_thread.start()

            # Give Flask time to start
            time.sleep(1.0)

            # Show native window (blocking call)
            native_window.show(block=True)
        else:
            # Browser mode - Flask runs in main thread
            run_flask_server()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        stop_scheduler()
        if hotkey_manager:
            hotkey_manager.stop()
        if status_window:
            status_window.destroy()
        if tray:
            tray.stop()
        if native_window and native_window.is_running:
            native_window.close()


if __name__ == "__main__":
    main()
