"""Singleton management for configuration.

This module provides the get_config() and reset_config() functions
for managing the configuration singleton instance.
"""

import threading
from pathlib import Path

from dotenv import load_dotenv

from mysql_to_sheets.core.config.dataclass import Config
from mysql_to_sheets.core.paths import find_env_file

_config: Config | None = None
_config_lock = threading.Lock()


def get_config(env_file: str | None = None) -> Config:
    """Load and return configuration singleton (thread-safe).

    Uses double-checked locking to ensure thread safety while minimizing
    lock contention after initialization.

    Provider Precedence:
        1. Context-scoped provider (set via set_config_provider or provider_context)
        2. Global singleton (environment-based)

    This maintains backward compatibility while enabling multi-tenant
    SaaS deployments with database-backed configuration.

    Args:
        env_file: Path to .env file. If None, searches standard locations:
            1. Current working directory
            2. Platform-specific config directory
            3. Executable directory (when bundled)
            4. Package root directory (development)

    Returns:
        Config instance.
    """
    global _config

    # Check for context-scoped provider first
    try:
        from mysql_to_sheets.core.config_factory import get_current_provider

        provider = get_current_provider()
        if provider is not None:
            return provider.get_config()
    except ImportError:
        # config_factory not available (shouldn't happen, but be safe)
        pass

    # Fast path: already initialized (no lock needed)
    if _config is not None:
        return _config

    # Slow path: acquire lock and initialize
    with _config_lock:
        # Double-check inside lock (another thread may have initialized)
        if _config is not None:
            return _config

        # Find .env file
        if env_file:
            env_path: Path | None = Path(env_file)
            if env_path and not env_path.is_absolute() and not env_path.exists():
                # Try package directory as fallback
                package_dir = Path(__file__).parent.parent.parent
                env_path = package_dir / env_file
        else:
            # Use smart path finding
            env_path = find_env_file()

        if env_path and env_path.exists():
            load_dotenv(env_path)

        _config = Config()
        return _config


def reset_config() -> None:
    """Reset config singleton (useful for testing). Thread-safe.

    Also resets the config provider factory.
    """
    global _config
    with _config_lock:
        _config = None

    # Reset provider factory
    try:
        from mysql_to_sheets.core.config_factory import reset_config_provider_factory

        reset_config_provider_factory()
    except ImportError:
        pass
