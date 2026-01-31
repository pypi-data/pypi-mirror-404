"""Global keyboard shortcuts for the desktop application.

This module provides cross-platform global hotkey support using pynput.
Hotkeys can be registered to trigger actions even when the app is not focused.
"""

import logging
import platform
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class HotkeyAction(Enum):
    """Predefined hotkey actions."""

    TRIGGER_SYNC = "trigger_sync"
    OPEN_DASHBOARD = "open_dashboard"
    TOGGLE_STATUS_WINDOW = "toggle_status_window"
    PAUSE_RESUME = "pause_resume"
    CHECK_FRESHNESS = "check_freshness"
    OPEN_SETTINGS = "open_settings"


@dataclass
class HotkeyBinding:
    """A keyboard shortcut binding.

    Attributes:
        action: The action this hotkey triggers.
        key: The main key (e.g., 's', 'd', 'p').
        modifiers: List of modifier keys ('ctrl', 'shift', 'alt', 'cmd').
        description: Human-readable description.
        enabled: Whether this binding is active.
    """

    action: HotkeyAction
    key: str
    modifiers: list[str] = field(default_factory=list)
    description: str = ""
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "action": self.action.value,
            "key": self.key,
            "modifiers": self.modifiers,
            "description": self.description,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HotkeyBinding":
        """Create from dictionary."""
        return cls(
            action=HotkeyAction(data["action"]),
            key=data["key"],
            modifiers=data.get("modifiers", []),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
        )

    @property
    def display_string(self) -> str:
        """Get human-readable string for the binding.

        Returns:
            String like "Cmd+Shift+S" or "Ctrl+Shift+S".
        """
        parts = []
        # Order modifiers: Ctrl/Cmd, Alt, Shift, then key
        for mod in ["ctrl", "cmd", "alt", "shift"]:
            if mod in self.modifiers:
                if mod == "ctrl":
                    parts.append("Ctrl" if platform.system() != "Darwin" else "^")
                elif mod == "cmd":
                    parts.append("Cmd" if platform.system() == "Darwin" else "Win")
                elif mod == "alt":
                    parts.append("Alt" if platform.system() != "Darwin" else "Opt")
                elif mod == "shift":
                    parts.append("Shift" if platform.system() != "Darwin" else "⇧")
        parts.append(self.key.upper())
        return "+".join(parts)


class GlobalHotkeyManager:
    """Manages global keyboard shortcuts.

    Uses pynput for cross-platform hotkey detection.
    """

    def __init__(self) -> None:
        """Initialize the hotkey manager."""
        self._bindings: dict[HotkeyAction, HotkeyBinding] = {}
        self._callbacks: dict[HotkeyAction, Callable[[], None]] = {}
        self._listener = None
        self._running = False
        self._lock = threading.Lock()
        self._pynput_available = False
        self._current_modifiers: set[str] = set()

        self._init_pynput()

    def _init_pynput(self) -> None:
        """Initialize pynput if available."""
        try:
            from pynput import keyboard

            self._pynput_available = True
            self._keyboard = keyboard
            logger.debug("Pynput keyboard initialized successfully")
        except ImportError:
            logger.warning(
                "Pynput not installed. Global hotkeys will be disabled. "
                "Install with: pip install pynput"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize pynput: {e}")

    @property
    def is_available(self) -> bool:
        """Check if hotkeys are available."""
        return self._pynput_available

    def register_binding(
        self,
        binding: HotkeyBinding,
        callback: Callable[[], None],
    ) -> bool:
        """Register a hotkey binding.

        Args:
            binding: The hotkey binding configuration.
            callback: Function to call when hotkey is triggered.

        Returns:
            True if registration succeeded.
        """
        with self._lock:
            self._bindings[binding.action] = binding
            self._callbacks[binding.action] = callback
            logger.debug(f"Registered hotkey: {binding.display_string} -> {binding.action.value}")
            return True

    def unregister_binding(self, action: HotkeyAction) -> bool:
        """Unregister a hotkey binding.

        Args:
            action: The action to unregister.

        Returns:
            True if binding was removed.
        """
        with self._lock:
            if action in self._bindings:
                del self._bindings[action]
                if action in self._callbacks:
                    del self._callbacks[action]
                logger.debug(f"Unregistered hotkey for: {action.value}")
                return True
            return False

    def get_binding(self, action: HotkeyAction) -> HotkeyBinding | None:
        """Get the binding for an action.

        Args:
            action: The action to look up.

        Returns:
            HotkeyBinding if found, None otherwise.
        """
        return self._bindings.get(action)

    def get_all_bindings(self) -> list[HotkeyBinding]:
        """Get all registered bindings.

        Returns:
            List of all bindings.
        """
        return list(self._bindings.values())

    def _normalize_key(self, key: Any) -> str | None:
        """Normalize a key to a string.

        Args:
            key: Key from pynput.

        Returns:
            Normalized key string or None.
        """
        try:
            # Handle special keys
            if hasattr(key, "char") and key.char:
                return key.char.lower()
            elif hasattr(key, "name"):
                return key.name.lower()
        except AttributeError:
            pass
        return None

    def _get_modifier_state(self, key: Any) -> str | None:
        """Get modifier name if key is a modifier.

        Args:
            key: Key from pynput.

        Returns:
            Modifier name or None.
        """
        if not hasattr(key, "name"):
            return None

        name = key.name.lower() if hasattr(key, "name") else None
        if not name:
            return None

        # Map key names to our modifier names
        modifier_map = {
            "ctrl": "ctrl",
            "ctrl_l": "ctrl",
            "ctrl_r": "ctrl",
            "shift": "shift",
            "shift_l": "shift",
            "shift_r": "shift",
            "alt": "alt",
            "alt_l": "alt",
            "alt_r": "alt",
            "alt_gr": "alt",
            "cmd": "cmd",
            "cmd_l": "cmd",
            "cmd_r": "cmd",
        }
        return modifier_map.get(name)

    def _on_press(self, key: Any) -> None:
        """Handle key press events."""
        # Track modifier state
        modifier = self._get_modifier_state(key)
        if modifier:
            self._current_modifiers.add(modifier)
            return

        # Get the actual key
        key_str = self._normalize_key(key)
        if not key_str:
            return

        # Check against all bindings
        with self._lock:
            for action, binding in self._bindings.items():
                if not binding.enabled:
                    continue

                # Check if key matches
                if binding.key.lower() != key_str:
                    continue

                # Check if all required modifiers are pressed
                required_mods = set(binding.modifiers)
                if required_mods == self._current_modifiers:
                    # Trigger callback in a thread to avoid blocking
                    callback = self._callbacks.get(action)
                    if callback:
                        threading.Thread(target=callback, daemon=True).start()
                        logger.debug(f"Hotkey triggered: {binding.display_string}")

    def _on_release(self, key: Any) -> None:
        """Handle key release events."""
        modifier = self._get_modifier_state(key)
        if modifier:
            self._current_modifiers.discard(modifier)

    def start(self) -> bool:
        """Start listening for hotkeys.

        Returns:
            True if listener started successfully.
        """
        if not self.is_available:
            logger.warning("Cannot start hotkey listener: pynput not available")
            return False

        if self._running:
            logger.warning("Hotkey listener already running")
            return True

        try:
            from pynput.keyboard import Listener

            self._listener = Listener(
                on_press=self._on_press,
                on_release=self._on_release,
            )
            self._listener.start()
            self._running = True
            logger.info("Global hotkey listener started")

            # Check for macOS accessibility permission
            if platform.system() == "Darwin":
                self._check_macos_permissions()

            return True

        except Exception as e:
            logger.error(f"Failed to start hotkey listener: {e}")
            return False

    def _check_macos_permissions(self) -> None:
        """Check if we have accessibility permissions on macOS."""
        try:
            import subprocess

            # Try to check trusted status (requires pyobjc)
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to keystroke ""',
                ],
                capture_output=True,
                timeout=2,
            )
            if result.returncode != 0:
                logger.warning(
                    "Global hotkeys may not work. Grant Accessibility permission "
                    "in System Preferences > Security & Privacy > Privacy > Accessibility"
                )
        except Exception:
            # Silently ignore - just a hint
            pass

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        if self._listener:
            try:
                self._listener.stop()
                self._running = False
                logger.info("Global hotkey listener stopped")
            except Exception as e:
                logger.warning(f"Error stopping hotkey listener: {e}")

    def is_running(self) -> bool:
        """Check if listener is running."""
        return self._running


# Global manager instance
_manager: GlobalHotkeyManager | None = None


def get_hotkey_manager() -> GlobalHotkeyManager:
    """Get or create the global hotkey manager.

    Returns:
        GlobalHotkeyManager instance.
    """
    global _manager
    if _manager is None:
        _manager = GlobalHotkeyManager()
    return _manager


def reset_hotkey_manager() -> None:
    """Reset the global hotkey manager. For testing."""
    global _manager
    if _manager is not None:
        _manager.stop()
    _manager = None
