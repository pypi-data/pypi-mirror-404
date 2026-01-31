"""CLI output utilities for consistent, enhanced terminal output.

This module provides:
- Spinner class for long-running operations
- ProgressBar class for streaming mode
- Color utilities for terminal output
- Enhanced table formatting

Uses only ANSI escape codes - no external dependencies.
"""

import os
import sys
import threading
import time
from typing import Any

# =============================================================================
# Color Support
# =============================================================================


def supports_color() -> bool:
    """Check if the terminal supports color output.

    Returns:
        True if colors should be used, False otherwise.
    """
    # NO_COLOR environment variable disables colors (https://no-color.org/)
    if os.getenv("NO_COLOR"):
        return False

    # FORCE_COLOR enables colors even in non-TTY
    if os.getenv("FORCE_COLOR"):
        return True

    # Check if stdout is a TTY
    if not hasattr(sys.stdout, "isatty"):
        return False

    return sys.stdout.isatty()


class Colors:
    """ANSI color codes for terminal output."""

    # Reset
    RESET = "\033[0m"

    # Regular colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # Bold colors
    BOLD = "\033[1m"
    BOLD_RED = "\033[1;31m"
    BOLD_GREEN = "\033[1;32m"
    BOLD_YELLOW = "\033[1;33m"
    BOLD_BLUE = "\033[1;34m"

    # Dimmed
    DIM = "\033[2m"

    @classmethod
    def enabled(cls) -> bool:
        """Check if colors are enabled."""
        return supports_color()


def colorize(text: str, color: str) -> str:
    """Apply color to text if colors are enabled.

    Args:
        text: The text to colorize.
        color: The color code to apply (from Colors class).

    Returns:
        Colorized text if colors are enabled, otherwise plain text.
    """
    if not supports_color():
        return text
    return f"{color}{text}{Colors.RESET}"


def success(text: str) -> str:
    """Format text as success (green)."""
    return colorize(text, Colors.GREEN)


def error(text: str) -> str:
    """Format text as error (red)."""
    return colorize(text, Colors.RED)


def warning(text: str) -> str:
    """Format text as warning (yellow)."""
    return colorize(text, Colors.YELLOW)


def info(text: str) -> str:
    """Format text as info (blue)."""
    return colorize(text, Colors.BLUE)


def dim(text: str) -> str:
    """Format text as dimmed (gray)."""
    return colorize(text, Colors.DIM)


def bold(text: str) -> str:
    """Format text as bold."""
    return colorize(text, Colors.BOLD)


# =============================================================================
# Spinner
# =============================================================================


class Spinner:
    """A terminal spinner for long-running operations.

    Usage:
        with Spinner("Connecting to database"):
            connect_to_database()

        # Or manually:
        spinner = Spinner("Processing")
        spinner.start()
        do_work()
        spinner.stop("Done!")
    """

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    INTERVAL = 0.08  # seconds between frames

    def __init__(self, message: str = "Processing") -> None:
        """Initialize the spinner.

        Args:
            message: The message to display next to the spinner.
        """
        self.message = message
        self._running = False
        self._thread: threading.Thread | None = None
        self._frame_index = 0
        self._enabled = supports_color() and sys.stdout.isatty()

    def start(self) -> "Spinner":
        """Start the spinner animation.

        Returns:
            Self for chaining.
        """
        if not self._enabled:
            print(f"{self.message}...", flush=True)
            return self

        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self

    def _animate(self) -> None:
        """Animation loop for the spinner."""
        while self._running:
            frame = self.FRAMES[self._frame_index]
            sys.stdout.write(f"\r{colorize(frame, Colors.CYAN)} {self.message}")
            sys.stdout.flush()
            self._frame_index = (self._frame_index + 1) % len(self.FRAMES)
            time.sleep(self.INTERVAL)

    def stop(self, final_message: str | None = None, success_status: bool = True) -> None:
        """Stop the spinner and display a final message.

        Args:
            final_message: Message to display when stopped. Defaults to original message.
            success_status: If True, shows green check; if False, shows red X.
        """
        self._running = False

        if self._thread:
            self._thread.join(timeout=0.2)

        if not self._enabled:
            if final_message:
                status = "OK" if success_status else "FAILED"
                print(f" [{status}] {final_message}")
            return

        # Clear the line
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")

        # Display final status
        if final_message:
            symbol = colorize("✓", Colors.GREEN) if success_status else colorize("✗", Colors.RED)
            print(f"{symbol} {final_message}")
        else:
            symbol = colorize("✓", Colors.GREEN) if success_status else colorize("✗", Colors.RED)
            print(f"{symbol} {self.message}")

    def __enter__(self) -> "Spinner":
        """Context manager entry."""
        return self.start()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        if exc_type:
            self.stop(f"{self.message} - Failed", success_status=False)
        else:
            self.stop(f"{self.message} - Done", success_status=True)


# =============================================================================
# Progress Bar
# =============================================================================


class ProgressBar:
    """A terminal progress bar for tracking progress.

    Usage:
        progress = ProgressBar(total=100, description="Syncing rows")
        for item in items:
            process(item)
            progress.update(1)
        progress.finish()
    """

    def __init__(
        self,
        total: int,
        description: str = "Progress",
        width: int = 40,
    ) -> None:
        """Initialize the progress bar.

        Args:
            total: Total number of items to process.
            description: Description to show before the bar.
            width: Width of the progress bar in characters.
        """
        self.total = total
        self.description = description
        self.width = width
        self.current = 0
        self._enabled = supports_color() and sys.stdout.isatty()
        self._start_time = time.time()

    def update(self, amount: int = 1) -> None:
        """Update progress by the given amount.

        Args:
            amount: Amount to increment by.
        """
        self.current = min(self.current + amount, self.total)
        self._render()

    def set(self, value: int) -> None:
        """Set progress to a specific value.

        Args:
            value: The new progress value.
        """
        self.current = min(value, self.total)
        self._render()

    def _render(self) -> None:
        """Render the progress bar to terminal."""
        if not self._enabled:
            return

        percent = self.current / self.total if self.total > 0 else 0
        filled = int(self.width * percent)
        bar = "█" * filled + "░" * (self.width - filled)

        # Calculate elapsed and ETA
        elapsed = time.time() - self._start_time
        if percent > 0:
            eta = elapsed / percent - elapsed
            eta_str = f"ETA: {int(eta)}s"
        else:
            eta_str = "ETA: --"

        line = (
            f"\r{self.description}: "
            f"{colorize(bar, Colors.CYAN)} "
            f"{percent:6.1%} "
            f"({self.current}/{self.total}) "
            f"{dim(eta_str)}"
        )
        sys.stdout.write(line)
        sys.stdout.flush()

    def finish(self, message: str | None = None) -> None:
        """Finish the progress bar.

        Args:
            message: Optional completion message.
        """
        if not self._enabled:
            if message:
                print(message)
            return

        # Set to 100%
        self.current = self.total
        self._render()
        print()  # New line

        if message:
            print(colorize("✓", Colors.GREEN) + f" {message}")


# =============================================================================
# Table Formatting
# =============================================================================


def format_table(
    headers: list[str],
    rows: list[list[Any]],
    widths: list[int] | None = None,
    max_width: int | None = None,
    truncate: bool = True,
) -> str:
    """Format data as a text table with optional truncation.

    Args:
        headers: Column headers.
        rows: Data rows.
        widths: Optional fixed column widths.
        max_width: Maximum total width (defaults to terminal width).
        truncate: Whether to truncate long values.

    Returns:
        Formatted table string.
    """
    if not rows:
        return "(no data)"

    # Calculate widths
    if widths is None:
        widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(val)))

    # Apply max_width if specified
    if max_width is None:
        try:
            max_width = os.get_terminal_size().columns - 4
        except OSError:
            max_width = 100

    total_width = sum(widths) + (len(widths) - 1) * 2
    if truncate and total_width > max_width:
        # Proportionally reduce column widths
        scale = max_width / total_width
        widths = [max(5, int(w * scale)) for w in widths]

    def truncate_cell(value: Any, width: int) -> str:
        s = str(value)
        if len(s) > width:
            return s[: width - 1] + "…"
        return s.ljust(width)

    lines = []

    # Header
    header_parts = [truncate_cell(h, widths[i]) for i, h in enumerate(headers)]
    if supports_color():
        lines.append(colorize("  ".join(header_parts), Colors.BOLD))
    else:
        lines.append("  ".join(header_parts))

    # Separator
    separator = "─" * (sum(widths) + 2 * (len(widths) - 1))
    lines.append(dim(separator) if supports_color() else "-" * len(separator))

    # Rows
    for row in rows:
        row_parts = [
            truncate_cell(row[i] if i < len(row) else "", widths[i]) for i in range(len(widths))
        ]
        lines.append("  ".join(row_parts))

    return "\n".join(lines)


def print_status(label: str, value: str, status: str = "info") -> None:
    """Print a status line with label and value.

    Args:
        label: The label text.
        value: The value text.
        status: Status type: 'success', 'error', 'warning', 'info'.
    """
    color_map = {
        "success": Colors.GREEN,
        "error": Colors.RED,
        "warning": Colors.YELLOW,
        "info": Colors.CYAN,
    }
    color = color_map.get(status, Colors.WHITE)

    if supports_color():
        print(f"  {dim(label + ':')} {colorize(value, color)}")
    else:
        print(f"  {label}: {value}")


def print_section(title: str) -> None:
    """Print a section header.

    Args:
        title: The section title.
    """
    if supports_color():
        print(f"\n{bold(title)}")
        print(dim("─" * len(title)))
    else:
        print(f"\n{title}")
        print("-" * len(title))
