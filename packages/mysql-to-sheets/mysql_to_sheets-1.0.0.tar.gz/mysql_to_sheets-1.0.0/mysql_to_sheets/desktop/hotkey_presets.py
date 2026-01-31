"""Default hotkey presets and conflict detection.

This module provides platform-aware default shortcuts and a database
of common system shortcuts to help avoid conflicts.
"""

import platform
from dataclasses import dataclass

from mysql_to_sheets.desktop.hotkeys import HotkeyAction, HotkeyBinding

# Platform detection
IS_MACOS = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"


def get_default_bindings() -> list[HotkeyBinding]:
    """Get default hotkey bindings for the current platform.

    Returns:
        List of default HotkeyBinding instances.
    """
    # Use Cmd on macOS, Ctrl on Windows/Linux
    primary_mod = "cmd" if IS_MACOS else "ctrl"

    return [
        HotkeyBinding(
            action=HotkeyAction.TRIGGER_SYNC,
            key="s",
            modifiers=[primary_mod, "shift"],
            description="Trigger manual sync",
            enabled=True,
        ),
        HotkeyBinding(
            action=HotkeyAction.OPEN_DASHBOARD,
            key="d",
            modifiers=[primary_mod, "shift"],
            description="Open dashboard in browser",
            enabled=True,
        ),
        HotkeyBinding(
            action=HotkeyAction.TOGGLE_STATUS_WINDOW,
            key="w",
            modifiers=[primary_mod, "shift"],
            description="Toggle status window",
            enabled=True,
        ),
        HotkeyBinding(
            action=HotkeyAction.PAUSE_RESUME,
            key="p",
            modifiers=[primary_mod, "shift"],
            description="Pause or resume syncs",
            enabled=True,
        ),
        HotkeyBinding(
            action=HotkeyAction.CHECK_FRESHNESS,
            key="f",
            modifiers=[primary_mod, "shift"],
            description="Check data freshness",
            enabled=False,  # Disabled by default
        ),
        HotkeyBinding(
            action=HotkeyAction.OPEN_SETTINGS,
            key="comma",
            modifiers=[primary_mod, "shift"],
            description="Open settings",
            enabled=False,  # Disabled by default
        ),
    ]


@dataclass
class ConflictInfo:
    """Information about a potential hotkey conflict."""

    shortcut: str  # e.g., "Cmd+Shift+S"
    application: str  # e.g., "macOS System"
    description: str  # e.g., "Save As"
    severity: str  # "warning" or "error"


# Database of common system shortcuts to check for conflicts
SYSTEM_SHORTCUTS: list[ConflictInfo] = [
    # macOS system shortcuts
    ConflictInfo("Cmd+S", "macOS System", "Save", "error"),
    ConflictInfo("Cmd+Shift+S", "macOS System", "Save As (some apps)", "warning"),
    ConflictInfo("Cmd+Q", "macOS System", "Quit Application", "error"),
    ConflictInfo("Cmd+W", "macOS System", "Close Window", "error"),
    ConflictInfo("Cmd+H", "macOS System", "Hide Application", "error"),
    ConflictInfo("Cmd+M", "macOS System", "Minimize Window", "error"),
    ConflictInfo("Cmd+Tab", "macOS System", "App Switcher", "error"),
    ConflictInfo("Cmd+Space", "macOS System", "Spotlight", "error"),
    ConflictInfo("Cmd+,", "macOS System", "Preferences", "warning"),
    ConflictInfo("Ctrl+Space", "macOS System", "Input Source", "warning"),

    # Windows system shortcuts
    ConflictInfo("Ctrl+S", "Windows System", "Save", "error"),
    ConflictInfo("Ctrl+Shift+S", "Windows System", "Save As (some apps)", "warning"),
    ConflictInfo("Win+D", "Windows System", "Show Desktop", "error"),
    ConflictInfo("Win+E", "Windows System", "File Explorer", "error"),
    ConflictInfo("Win+L", "Windows System", "Lock Screen", "error"),
    ConflictInfo("Win+Tab", "Windows System", "Task View", "error"),
    ConflictInfo("Alt+Tab", "Windows System", "Window Switcher", "error"),
    ConflictInfo("Ctrl+Alt+Del", "Windows System", "Security Options", "error"),

    # Linux/GNOME common shortcuts
    ConflictInfo("Ctrl+S", "Linux/GNOME", "Save", "error"),
    ConflictInfo("Super+D", "Linux/GNOME", "Show Desktop", "error"),
    ConflictInfo("Alt+F2", "Linux/GNOME", "Run Dialog", "warning"),
    ConflictInfo("Super+L", "Linux/GNOME", "Lock Screen", "error"),

    # Common application shortcuts
    ConflictInfo("Ctrl+Shift+P", "VS Code", "Command Palette", "warning"),
    ConflictInfo("Cmd+Shift+P", "VS Code", "Command Palette", "warning"),
    ConflictInfo("Ctrl+Shift+F", "VS Code/Browser", "Find in Files/Page Search", "warning"),
    ConflictInfo("Cmd+Shift+F", "VS Code/Browser", "Find in Files/Page Search", "warning"),
]


def check_conflicts(binding: HotkeyBinding) -> list[ConflictInfo]:
    """Check if a binding conflicts with known system shortcuts.

    Args:
        binding: The binding to check.

    Returns:
        List of potential conflicts.
    """
    conflicts = []
    shortcut = binding.display_string

    for system_shortcut in SYSTEM_SHORTCUTS:
        # Normalize for comparison
        s1 = _normalize_shortcut(shortcut)
        s2 = _normalize_shortcut(system_shortcut.shortcut)

        if s1 == s2:
            # Check platform relevance
            app = system_shortcut.application.lower()
            if IS_MACOS and ("windows" in app or "linux" in app or "gnome" in app):
                continue
            if IS_WINDOWS and ("macos" in app or "linux" in app or "gnome" in app):
                continue
            if IS_LINUX and ("macos" in app or "windows" in app):
                continue

            conflicts.append(system_shortcut)

    return conflicts


def _normalize_shortcut(shortcut: str) -> str:
    """Normalize a shortcut string for comparison.

    Args:
        shortcut: Shortcut string like "Cmd+Shift+S".

    Returns:
        Normalized lowercase string.
    """
    # Convert to lowercase and sort modifiers
    parts = shortcut.lower().replace(" ", "").split("+")
    key = parts[-1] if parts else ""
    mods = sorted(parts[:-1]) if len(parts) > 1 else []

    # Normalize modifier names
    normalized_mods = []
    for mod in mods:
        if mod in ("ctrl", "control", "^"):
            normalized_mods.append("ctrl")
        elif mod in ("cmd", "command", "meta", "super", "win"):
            normalized_mods.append("cmd")
        elif mod in ("alt", "opt", "option"):
            normalized_mods.append("alt")
        elif mod in ("shift", "⇧"):
            normalized_mods.append("shift")
        else:
            normalized_mods.append(mod)

    normalized_mods.sort()
    return "+".join(normalized_mods + [key])


def get_platform_modifier_name() -> str:
    """Get the platform-specific primary modifier name.

    Returns:
        "Cmd" on macOS, "Ctrl" on Windows/Linux.
    """
    return "Cmd" if IS_MACOS else "Ctrl"


def format_shortcut_for_display(binding: HotkeyBinding) -> str:
    """Format a binding for display in the UI.

    Args:
        binding: The binding to format.

    Returns:
        Formatted string like "⌘⇧S" on macOS or "Ctrl+Shift+S" elsewhere.
    """
    if IS_MACOS:
        # Use macOS-style symbols
        symbols = []
        for mod in ["ctrl", "alt", "shift", "cmd"]:
            if mod in binding.modifiers:
                if mod == "ctrl":
                    symbols.append("⌃")
                elif mod == "alt":
                    symbols.append("⌥")
                elif mod == "shift":
                    symbols.append("⇧")
                elif mod == "cmd":
                    symbols.append("⌘")
        symbols.append(binding.key.upper())
        return "".join(symbols)
    else:
        return binding.display_string
