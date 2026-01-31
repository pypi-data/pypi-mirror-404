"""Auto-update checker for MySQL to Sheets Sync desktop application.

Checks GitHub Releases API for newer versions and notifies the user.

Usage:
    from mysql_to_sheets.desktop.updater import UpdateChecker

    checker = UpdateChecker()
    update_info = checker.check_for_updates()
    if update_info:
        print(f"New version available: {update_info['version']}")
"""

import json
import logging
import platform
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from typing import Callable
from urllib.error import URLError
from urllib.request import Request, urlopen

from mysql_to_sheets import __version__

logger = logging.getLogger(__name__)

# GitHub repository info
GITHUB_OWNER = "BrandonFricke"
GITHUB_REPO = "mysql-to-sheets"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

# Check interval (default: once per day)
DEFAULT_CHECK_INTERVAL_HOURS = 24


@dataclass
class UpdateInfo:
    """Information about an available update."""

    version: str
    release_url: str
    download_url: str
    release_notes: str
    published_at: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "release_url": self.release_url,
            "download_url": self.download_url,
            "release_notes": self.release_notes,
            "published_at": self.published_at,
        }


def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse version string into tuple for comparison.

    Args:
        version_str: Version like "1.0.0" or "v1.0.0"

    Returns:
        Tuple of version parts (1, 0, 0)
    """
    # Strip leading 'v' if present
    if version_str.startswith("v"):
        version_str = version_str[1:]

    # Split and convert to integers
    try:
        return tuple(int(part) for part in version_str.split(".")[:3])
    except ValueError:
        return (0, 0, 0)


def is_newer_version(latest: str, current: str) -> bool:
    """Check if latest version is newer than current.

    Args:
        latest: Latest version string.
        current: Current version string.

    Returns:
        True if latest is newer.
    """
    return parse_version(latest) > parse_version(current)


def get_platform_asset_name() -> str:
    """Get the expected asset filename for the current platform.

    Returns:
        Asset filename pattern to look for.
    """
    system = platform.system().lower()

    if system == "darwin":
        return "macos.dmg"
    elif system == "windows":
        return "windows-setup.exe"
    elif system == "linux":
        return "x86_64.AppImage"
    else:
        return ""


class UpdateChecker:
    """Checks for application updates from GitHub releases.

    Features:
    - Manual update check
    - Automatic background checking (optional)
    - Callback notification when update is available
    """

    def __init__(
        self,
        on_update_available: Callable[[UpdateInfo], None] | None = None,
        check_interval_hours: float = DEFAULT_CHECK_INTERVAL_HOURS,
    ) -> None:
        """Initialize the update checker.

        Args:
            on_update_available: Callback when an update is found.
            check_interval_hours: Hours between automatic checks.
        """
        self._on_update_available = on_update_available
        self._check_interval = check_interval_hours * 3600  # Convert to seconds
        self._last_check_time: float = 0
        self._last_update_info: UpdateInfo | None = None
        self._background_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._current_version = __version__

    @property
    def current_version(self) -> str:
        """Get the current application version."""
        return self._current_version

    @property
    def last_update_info(self) -> UpdateInfo | None:
        """Get the last found update info."""
        return self._last_update_info

    def check_for_updates(self, force: bool = False) -> UpdateInfo | None:
        """Check GitHub releases for a newer version.

        Args:
            force: Force check even if within check interval.

        Returns:
            UpdateInfo if a newer version is available, None otherwise.
        """
        # Rate limit checks unless forced
        now = time.time()
        if not force and (now - self._last_check_time) < self._check_interval:
            return self._last_update_info

        self._last_check_time = now
        logger.info(f"Checking for updates (current: {self._current_version})")

        try:
            # Fetch latest release from GitHub API
            request = Request(
                RELEASES_API_URL,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": f"mysql-to-sheets/{self._current_version}",
                },
            )

            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            # Extract version from tag
            latest_version = data.get("tag_name", "")
            if not latest_version:
                logger.warning("No tag_name in release response")
                return None

            # Check if newer
            if not is_newer_version(latest_version, self._current_version):
                logger.info(f"No update available (latest: {latest_version})")
                self._last_update_info = None
                return None

            # Find download URL for current platform
            platform_asset = get_platform_asset_name()
            download_url = data.get("html_url", "")  # Default to release page

            if platform_asset:
                for asset in data.get("assets", []):
                    if platform_asset in asset.get("name", ""):
                        download_url = asset.get("browser_download_url", download_url)
                        break

            # Create update info
            update_info = UpdateInfo(
                version=latest_version.lstrip("v"),
                release_url=data.get("html_url", ""),
                download_url=download_url,
                release_notes=data.get("body", "")[:500],  # Truncate long notes
                published_at=data.get("published_at", ""),
            )

            self._last_update_info = update_info
            logger.info(f"Update available: {update_info.version}")

            # Notify callback
            if self._on_update_available:
                try:
                    self._on_update_available(update_info)
                except Exception as e:
                    logger.error(f"Update callback failed: {e}")

            return update_info

        except URLError as e:
            logger.warning(f"Failed to check for updates: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid response from GitHub: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error checking for updates: {e}")
            return None

    def open_download_page(self) -> None:
        """Open the download page for the latest update in the browser."""
        if self._last_update_info:
            url = self._last_update_info.download_url or self._last_update_info.release_url
            webbrowser.open(url)
        else:
            # Open releases page
            webbrowser.open(f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases")

    def start_background_checker(self) -> None:
        """Start automatic background update checking."""
        if self._background_thread and self._background_thread.is_alive():
            return

        self._stop_event.clear()

        def _check_loop() -> None:
            # Initial check after startup delay
            time.sleep(30)  # Wait 30 seconds after app start

            while not self._stop_event.is_set():
                self.check_for_updates()
                # Sleep in chunks to allow quick shutdown
                for _ in range(int(self._check_interval / 60)):
                    if self._stop_event.is_set():
                        break
                    time.sleep(60)

        self._background_thread = threading.Thread(target=_check_loop, daemon=True)
        self._background_thread.start()
        logger.info("Background update checker started")

    def stop_background_checker(self) -> None:
        """Stop the background update checker."""
        self._stop_event.set()
        if self._background_thread:
            self._background_thread.join(timeout=5)
        logger.info("Background update checker stopped")


# Global instance
_checker: UpdateChecker | None = None


def get_update_checker(
    on_update_available: Callable[[UpdateInfo], None] | None = None,
) -> UpdateChecker:
    """Get or create the global update checker instance.

    Args:
        on_update_available: Callback for update notifications.

    Returns:
        UpdateChecker instance.
    """
    global _checker
    if _checker is None:
        _checker = UpdateChecker(on_update_available=on_update_available)
    return _checker
