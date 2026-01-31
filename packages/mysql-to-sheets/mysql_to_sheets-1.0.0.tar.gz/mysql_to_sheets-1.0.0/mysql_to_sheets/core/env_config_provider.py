"""Environment-based configuration provider.

Implements ConfigProvider using environment variables and .env files.
This is the default provider for CLI usage and backward compatibility.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

from mysql_to_sheets.core.config_provider import ConfigProvider
from mysql_to_sheets.core.paths import find_env_file

if TYPE_CHECKING:
    from mysql_to_sheets.core.config import Config


class EnvConfigProvider(ConfigProvider):
    """Configuration provider that reads from environment variables.

    Loads configuration from:
    1. Environment variables (takes precedence)
    2. .env file in standard locations

    This is the default provider and maintains backward compatibility
    with the existing get_config() singleton pattern.

    Example::

        # Default .env location
        provider = EnvConfigProvider()
        config = provider.get_config()

        # Custom .env file
        provider = EnvConfigProvider(env_file="/path/to/.env")
        config = provider.get_config()

        # Refresh after environment changes
        config = provider.refresh()
    """

    def __init__(self, env_file: str | Path | None = None) -> None:
        """Initialize environment provider.

        Args:
            env_file: Optional path to .env file. If None, searches
                standard locations (cwd, config dir, package root).
        """
        self._env_file = env_file
        self._config: "Config | None" = None
        self._env_loaded = False

    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        if self._env_loaded:
            return

        # Find .env file
        if self._env_file:
            env_path: Path | None = Path(self._env_file)
            if env_path and not env_path.is_absolute() and not env_path.exists():
                # Try package directory as fallback
                package_dir = Path(__file__).parent.parent.parent
                env_path = package_dir / self._env_file
        else:
            # Use smart path finding
            env_path = find_env_file()

        if env_path and env_path.exists():
            load_dotenv(env_path, override=True)

        self._env_loaded = True

    def get_config(self) -> "Config":
        """Get configuration from environment variables.

        Returns:
            Config instance populated from environment.
        """
        if self._config is not None:
            return self._config

        self._load_env()

        # Import here to avoid circular import
        from mysql_to_sheets.core.config import Config

        self._config = Config()
        return self._config

    def refresh(self) -> "Config":
        """Reload configuration from environment.

        Clears cached config and reloads from environment.

        Returns:
            Freshly loaded Config instance.
        """
        self._config = None
        self._env_loaded = False
        return self.get_config()

    @property
    def provider_type(self) -> str:
        """Get provider type identifier.

        Returns:
            'env' for environment-based provider.
        """
        return "env"

    @property
    def env_file(self) -> str | Path | None:
        """Get the configured .env file path."""
        return self._env_file
