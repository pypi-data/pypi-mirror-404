"""Native window wrapper using pywebview.

This module provides a native desktop window experience instead of
opening the dashboard in a web browser. The window integrates with
the system tray and supports minimize-to-tray behavior.

Platform notes:
    - macOS: Uses WebKit (built-in)
    - Windows: Uses Edge WebView2 (pre-installed on Win10/11)
    - Linux: Uses GTK WebKit (requires libwebkit2gtk-4.0)

Example:
    >>> from mysql_to_sheets.desktop.window import DesktopWindow
    >>>
    >>> window = DesktopWindow(
    ...     title="MySQL to Sheets",
    ...     url="http://127.0.0.1:5000/login",
    ...     width=1200,
    ...     height=800,
    ... )
    >>> window.show()  # Blocking call
"""

import logging
import threading
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    import webview

logger = logging.getLogger(__name__)


class DesktopWindow:
    """Native window wrapper using pywebview.

    Provides a native desktop window experience for the web dashboard.
    Supports minimize-to-tray and restore-from-tray operations.

    Attributes:
        is_available: Whether pywebview is available on this platform.
    """

    def __init__(
        self,
        title: str,
        url: str,
        width: int = 1200,
        height: int = 800,
        min_width: int = 800,
        min_height: int = 600,
        on_closed: Callable[[], None] | None = None,
        on_loaded: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the native window.

        Args:
            title: Window title.
            url: URL to load in the window.
            width: Initial window width in pixels.
            height: Initial window height in pixels.
            min_width: Minimum window width.
            min_height: Minimum window height.
            on_closed: Callback when window is closed (not minimized).
            on_loaded: Callback when page finishes loading.
        """
        self._title = title
        self._url = url
        self._width = width
        self._height = height
        self._min_width = min_width
        self._min_height = min_height
        self._on_closed = on_closed
        self._on_loaded = on_loaded

        self._window: "webview.Window | None" = None
        self._is_available = False
        self._is_running = False
        self._lock = threading.Lock()

        self._check_availability()

    def _check_availability(self) -> None:
        """Check if pywebview is available."""
        try:
            import webview

            self._is_available = True
            logger.debug("pywebview is available")
        except ImportError:
            logger.warning(
                "pywebview not installed. Native window unavailable. "
                "Install with: pip install pywebview"
            )

    @property
    def is_available(self) -> bool:
        """Check if native window is available."""
        return self._is_available

    @property
    def is_running(self) -> bool:
        """Check if the window is currently running."""
        return self._is_running

    def show(self, block: bool = True) -> None:
        """Create and show the native window.

        Args:
            block: If True (default), blocks until window is closed.
                   If False, runs in a background thread.

        Raises:
            RuntimeError: If pywebview is not available.
        """
        if not self._is_available:
            raise RuntimeError("pywebview is not available. Install with: pip install pywebview")

        if block:
            self._run_window()
        else:
            thread = threading.Thread(target=self._run_window, daemon=True, name="webview-window")
            thread.start()

    def _run_window(self) -> None:
        """Internal method to create and run the window."""
        import webview

        with self._lock:
            if self._is_running:
                logger.warning("Window is already running")
                return
            self._is_running = True

        try:
            # Create the window
            self._window = webview.create_window(
                self._title,
                self._url,
                width=self._width,
                height=self._height,
                min_size=(self._min_width, self._min_height),
                resizable=True,
                text_select=True,
            )

            # Register event handlers
            if self._on_loaded:
                self._window.events.loaded += self._on_loaded

            if self._on_closed:
                self._window.events.closed += self._on_closed

            logger.info(f"Starting native window: {self._url}")

            # Start the webview event loop (blocking)
            webview.start()

        except Exception as e:
            logger.error(f"Failed to start native window: {e}")
            raise
        finally:
            with self._lock:
                self._is_running = False
                self._window = None

    def hide(self) -> None:
        """Hide (minimize) the window.

        The window remains in memory and can be restored with show().
        This is used for minimize-to-tray behavior.
        """
        if self._window:
            try:
                self._window.hide()
                logger.debug("Window hidden")
            except Exception as e:
                logger.warning(f"Failed to hide window: {e}")

    def restore(self) -> None:
        """Restore a hidden window.

        Brings the window back to the foreground after it was
        hidden with hide().
        """
        if self._window:
            try:
                self._window.show()
                logger.debug("Window restored")
            except Exception as e:
                logger.warning(f"Failed to restore window: {e}")

    def minimize(self) -> None:
        """Minimize the window to the taskbar/dock."""
        if self._window:
            try:
                self._window.minimize()
                logger.debug("Window minimized")
            except Exception as e:
                logger.warning(f"Failed to minimize window: {e}")

    def maximize(self) -> None:
        """Maximize the window."""
        if self._window:
            try:
                # pywebview uses toggle_fullscreen for maximize
                self._window.toggle_fullscreen()
                logger.debug("Window maximized")
            except Exception as e:
                logger.warning(f"Failed to maximize window: {e}")

    def close(self) -> None:
        """Close the window and stop the webview event loop.

        This is a permanent close - the window cannot be restored
        after calling this method.
        """
        if self._window:
            try:
                self._window.destroy()
                logger.info("Window closed")
            except Exception as e:
                logger.warning(f"Failed to close window: {e}")

    def set_title(self, title: str) -> None:
        """Update the window title.

        Args:
            title: New window title.
        """
        if self._window:
            try:
                self._window.set_title(title)
            except Exception as e:
                logger.warning(f"Failed to set title: {e}")

    def load_url(self, url: str) -> None:
        """Navigate to a different URL.

        Args:
            url: URL to load.
        """
        if self._window:
            try:
                self._window.load_url(url)
            except Exception as e:
                logger.warning(f"Failed to load URL: {e}")

    def evaluate_js(self, script: str) -> Any:
        """Execute JavaScript in the window.

        Args:
            script: JavaScript code to execute.

        Returns:
            Result of the JavaScript execution.
        """
        if self._window:
            try:
                return self._window.evaluate_js(script)
            except Exception as e:
                logger.warning(f"Failed to evaluate JS: {e}")
                return None
        return None


# Global window instance for singleton access
_window: DesktopWindow | None = None
_window_lock = threading.Lock()


def get_desktop_window(
    title: str = "MySQL to Sheets",
    url: str = "http://127.0.0.1:5000",
    width: int = 1200,
    height: int = 800,
    on_closed: Callable[[], None] | None = None,
    on_loaded: Callable[[], None] | None = None,
) -> DesktopWindow:
    """Get or create the global desktop window instance.

    Creates a singleton window instance. Subsequent calls with
    different parameters will be ignored (use the existing window).

    Args:
        title: Window title.
        url: URL to load.
        width: Window width.
        height: Window height.
        on_closed: Callback when window is closed.
        on_loaded: Callback when page loads.

    Returns:
        The global DesktopWindow instance.
    """
    global _window
    with _window_lock:
        if _window is None:
            _window = DesktopWindow(
                title=title,
                url=url,
                width=width,
                height=height,
                on_closed=on_closed,
                on_loaded=on_loaded,
            )
        return _window


def reset_desktop_window() -> None:
    """Reset the global window instance (for testing)."""
    global _window
    with _window_lock:
        if _window and _window.is_running:
            _window.close()
        _window = None
