"""Status window for the desktop application.

This module provides a persistent status window showing real-time sync status,
progress information, and upcoming scheduled syncs.
"""

import logging
import threading
import time
from datetime import datetime
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from mysql_to_sheets.desktop.background import BackgroundSyncManager, SyncProgress

logger = logging.getLogger(__name__)


class StatusWindow:
    """Persistent status window showing sync state and upcoming syncs.

    Features:
    - Current status indicator (Ready/Syncing/Error/Paused)
    - Progress bar with phase label
    - Last sync info card
    - Upcoming scheduled syncs list
    - Minimize to tray (hide window, don't close)
    """

    def __init__(
        self,
        on_minimize: Callable[[], None] | None = None,
        on_sync_now: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the status window.

        Args:
            on_minimize: Callback when minimize button is clicked.
            on_sync_now: Callback when "Sync Now" button is clicked.
        """
        self._on_minimize = on_minimize
        self._on_sync_now = on_sync_now
        self._window = None
        self._is_visible = False
        self._thread: threading.Thread | None = None

        # UI elements (set when window is created)
        self._status_label = None
        self._status_badge = None
        self._progress_bar = None
        self._progress_label = None
        self._last_sync_frame = None
        self._last_rows_label = None
        self._last_duration_label = None
        self._last_time_label = None
        self._upcoming_listbox = None
        self._sync_btn = None

        # State
        self._current_status = "ready"
        self._last_rows = 0
        self._last_duration = 0.0
        self._last_sync_time: datetime | None = None

        self._ttkbootstrap_available = self._check_ttkbootstrap()

    def _check_ttkbootstrap(self) -> bool:
        """Check if ttkbootstrap is available."""
        try:
            import ttkbootstrap  # noqa: F401

            return True
        except ImportError:
            logger.warning(
                "ttkbootstrap not installed. Status window will be disabled. "
                "Install with: pip install ttkbootstrap"
            )
            return False

    @property
    def is_available(self) -> bool:
        """Check if the status window is available."""
        return self._ttkbootstrap_available

    def _create_window(self) -> None:
        """Create the status window UI."""
        import ttkbootstrap as ttk
        from ttkbootstrap.constants import (
            BOTH,
            BOTTOM,
            DISABLED,
            END,
            HORIZONTAL,
            LEFT,
            NORMAL,
            RIGHT,
            TOP,
            W,
            X,
            Y,
        )

        # Create main window
        self._window = ttk.Window(themename="darkly")
        self._window.title("MySQL to Sheets - Status")
        self._window.geometry("420x550")
        self._window.resizable(False, False)

        # Handle window close - hide instead of destroy
        self._window.protocol("WM_DELETE_WINDOW", self._on_close)

        # Main container with padding
        main_frame = ttk.Frame(self._window, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        # ===== Status Section =====
        status_frame = ttk.LabelFrame(main_frame, text="Current Status", padding=15)
        status_frame.pack(fill=X, pady=(0, 15))

        # Status indicator row
        status_row = ttk.Frame(status_frame)
        status_row.pack(fill=X)

        self._status_badge = ttk.Label(
            status_row,
            text="●",
            font=("", 16),
            foreground="#4ade80",  # Green
        )
        self._status_badge.pack(side=LEFT, padx=(0, 10))

        self._status_label = ttk.Label(
            status_row,
            text="Ready",
            font=("", 14, "bold"),
        )
        self._status_label.pack(side=LEFT)

        # Sync Now button
        self._sync_btn = ttk.Button(
            status_row,
            text="Sync Now",
            bootstyle="success-outline",
            command=self._on_sync_click,
        )
        self._sync_btn.pack(side=RIGHT)

        # Progress bar
        progress_frame = ttk.Frame(status_frame)
        progress_frame.pack(fill=X, pady=(15, 5))

        self._progress_bar = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            bootstyle="success-striped",
            length=300,
        )
        self._progress_bar.pack(fill=X)

        self._progress_label = ttk.Label(
            status_frame,
            text="",
            font=("", 10),
            foreground="#94a3b8",
        )
        self._progress_label.pack(anchor=W)

        # ===== Last Sync Section =====
        self._last_sync_frame = ttk.LabelFrame(main_frame, text="Last Sync", padding=15)
        self._last_sync_frame.pack(fill=X, pady=(0, 15))

        # Stats row
        stats_frame = ttk.Frame(self._last_sync_frame)
        stats_frame.pack(fill=X)

        # Rows synced
        rows_frame = ttk.Frame(stats_frame)
        rows_frame.pack(side=LEFT, expand=True)
        ttk.Label(rows_frame, text="Rows", font=("", 9), foreground="#94a3b8").pack()
        self._last_rows_label = ttk.Label(rows_frame, text="—", font=("", 18, "bold"))
        self._last_rows_label.pack()

        # Duration
        duration_frame = ttk.Frame(stats_frame)
        duration_frame.pack(side=LEFT, expand=True)
        ttk.Label(duration_frame, text="Duration", font=("", 9), foreground="#94a3b8").pack()
        self._last_duration_label = ttk.Label(duration_frame, text="—", font=("", 18, "bold"))
        self._last_duration_label.pack()

        # Time
        time_frame = ttk.Frame(stats_frame)
        time_frame.pack(side=LEFT, expand=True)
        ttk.Label(time_frame, text="Time", font=("", 9), foreground="#94a3b8").pack()
        self._last_time_label = ttk.Label(time_frame, text="—", font=("", 18, "bold"))
        self._last_time_label.pack()

        # ===== Upcoming Syncs Section =====
        upcoming_frame = ttk.LabelFrame(main_frame, text="Upcoming Scheduled Syncs", padding=15)
        upcoming_frame.pack(fill=BOTH, expand=True, pady=(0, 15))

        # Listbox for upcoming syncs
        self._upcoming_listbox = ttk.Treeview(
            upcoming_frame,
            columns=("name", "next_run"),
            show="headings",
            height=5,
            bootstyle="dark",
        )
        self._upcoming_listbox.heading("name", text="Config")
        self._upcoming_listbox.heading("next_run", text="Next Run")
        self._upcoming_listbox.column("name", width=180)
        self._upcoming_listbox.column("next_run", width=180)
        self._upcoming_listbox.pack(fill=BOTH, expand=True)

        # Placeholder text
        self._upcoming_listbox.insert("", END, values=("No schedules configured", "—"))

        # ===== Footer =====
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=X)

        ttk.Button(
            footer_frame,
            text="Minimize to Tray",
            bootstyle="secondary-outline",
            command=self._on_close,
        ).pack(side=RIGHT)

        ttk.Label(
            footer_frame,
            text="MySQL to Sheets",
            font=("", 9),
            foreground="#64748b",
        ).pack(side=LEFT)

    def _on_close(self) -> None:
        """Handle window close - hide instead of destroy."""
        self.hide()
        if self._on_minimize:
            self._on_minimize()

    def _on_sync_click(self) -> None:
        """Handle sync button click."""
        if self._on_sync_now:
            self._on_sync_now()

    def show(self) -> None:
        """Show the status window."""
        if not self.is_available:
            logger.warning("Status window not available (ttkbootstrap not installed)")
            return

        if self._window is None:
            self._create_window()

        if self._window:
            self._window.deiconify()
            self._window.lift()
            self._window.focus_force()
            self._is_visible = True

    def hide(self) -> None:
        """Hide the status window."""
        if self._window:
            self._window.withdraw()
            self._is_visible = False

    @property
    def is_visible(self) -> bool:
        """Check if the window is currently visible."""
        return self._is_visible

    def toggle(self) -> None:
        """Toggle window visibility."""
        if self._is_visible:
            self.hide()
        else:
            self.show()

    def update_status(self, status: str, message: str = "") -> None:
        """Update the status indicator.

        Args:
            status: Status type ("ready", "syncing", "error", "paused").
            message: Optional status message.
        """
        if not self._window or not self._status_label:
            return

        self._current_status = status

        # Status colors and labels
        status_config = {
            "ready": ("Ready", "#4ade80", "success"),  # Green
            "syncing": ("Syncing", "#facc15", "warning"),  # Yellow
            "error": ("Error", "#f87171", "danger"),  # Red
            "paused": ("Paused", "#94a3b8", "secondary"),  # Gray
        }

        label, color, bootstyle = status_config.get(status, status_config["ready"])

        # Update in main thread
        def _update():
            if self._status_label:
                self._status_label.configure(text=label)
            if self._status_badge:
                self._status_badge.configure(foreground=color)
            if self._sync_btn:
                # Disable sync button while syncing
                if status == "syncing":
                    self._sync_btn.configure(state="disabled")
                else:
                    self._sync_btn.configure(state="normal")

        if self._window:
            self._window.after(0, _update)

    def update_progress(self, percent: int, phase: str, message: str = "") -> None:
        """Update the progress bar and phase label.

        Args:
            percent: Progress percentage (0-100).
            phase: Current phase name ("connecting", "fetching", "pushing", "complete").
            message: Optional progress message.
        """
        if not self._window:
            return

        # Phase labels
        phase_labels = {
            "connecting": "Connecting to database...",
            "fetching": "Fetching data...",
            "pushing": "Pushing to Google Sheets...",
            "complete": "Sync complete!",
        }

        display_message = message or phase_labels.get(phase, phase)

        def _update():
            if self._progress_bar:
                self._progress_bar.configure(value=percent)
            if self._progress_label:
                self._progress_label.configure(text=display_message)

        if self._window:
            self._window.after(0, _update)

    def update_last_sync(
        self,
        rows: int,
        duration_seconds: float,
        sync_time: datetime | None = None,
    ) -> None:
        """Update the last sync info card.

        Args:
            rows: Number of rows synced.
            duration_seconds: Sync duration in seconds.
            sync_time: When the sync completed.
        """
        if not self._window:
            return

        self._last_rows = rows
        self._last_duration = duration_seconds
        self._last_sync_time = sync_time or datetime.now()

        def _update():
            if self._last_rows_label:
                self._last_rows_label.configure(text=f"{rows:,}")
            if self._last_duration_label:
                self._last_duration_label.configure(text=f"{duration_seconds:.1f}s")
            if self._last_time_label:
                self._last_time_label.configure(text=self._format_time_ago())

        if self._window:
            self._window.after(0, _update)

    def _format_time_ago(self) -> str:
        """Format the last sync time as relative time."""
        if not self._last_sync_time:
            return "—"

        elapsed = (datetime.now() - self._last_sync_time).total_seconds()

        if elapsed < 60:
            return "Just now"
        elif elapsed < 3600:
            mins = int(elapsed / 60)
            return f"{mins}m ago"
        elif elapsed < 86400:
            hours = int(elapsed / 3600)
            return f"{hours}h ago"
        else:
            days = int(elapsed / 86400)
            return f"{days}d ago"

    def set_upcoming_syncs(self, syncs: list[dict]) -> None:
        """Update the upcoming syncs list.

        Args:
            syncs: List of dicts with "name" and "next_run" keys.
        """
        if not self._window or not self._upcoming_listbox:
            return

        def _update():
            # Clear existing items
            for item in self._upcoming_listbox.get_children():
                self._upcoming_listbox.delete(item)

            if not syncs:
                self._upcoming_listbox.insert("", "end", values=("No schedules configured", "—"))
            else:
                for sync in syncs[:5]:  # Show max 5
                    name = sync.get("name", "Unknown")
                    next_run = sync.get("next_run", "—")
                    self._upcoming_listbox.insert("", "end", values=(name, next_run))

        if self._window:
            self._window.after(0, _update)

    def run(self) -> None:
        """Start the window main loop (blocking)."""
        if not self.is_available:
            return

        if self._window is None:
            self._create_window()

        if self._window:
            self._is_visible = True
            self._window.mainloop()

    def start_background(self) -> None:
        """Start the window in a background thread."""
        if not self.is_available:
            return

        def _run():
            self.run()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def destroy(self) -> None:
        """Destroy the window completely."""
        if self._window:
            try:
                self._window.destroy()
            except Exception:
                pass
            self._window = None
            self._is_visible = False


# Convenience function for creating status window
def create_status_window(
    on_minimize: Callable[[], None] | None = None,
    on_sync_now: Callable[[], None] | None = None,
) -> StatusWindow | None:
    """Create a status window if ttkbootstrap is available.

    Args:
        on_minimize: Callback when minimize is clicked.
        on_sync_now: Callback when sync now is clicked.

    Returns:
        StatusWindow instance or None if ttkbootstrap not available.
    """
    window = StatusWindow(on_minimize=on_minimize, on_sync_now=on_sync_now)
    if window.is_available:
        return window
    return None
