"""Configuration management module for Windows Package Manager."""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .logger import logger


class Config:
    """Configuration manager with file-based settings storage."""

    def __init__(self, config_file: str = "config.json") -> None:
        """Initialize configuration manager.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = Path(config_file)
        self._config: Dict[str, Any] = self._load_default_config()
        self._load_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values.

        Returns:
            Dictionary containing default configuration
        """
        return {
            "app": {
                "name": "Windows Package Manager",
                "version": "1.0.0",
                "window": {
                    "width": 800,
                    "height": 600,
                    "resizable": True,
                },
                "theme": "default",
            },
            "winget": {
                "timeout": 300,  # seconds
                "retry_attempts": 3,
                "silent_install": True,
                "accept_agreements": True,
            },
            "logging": {
                "level": "INFO",
                "max_log_files": 30,
                "file_size_mb": 10,
            },
            "database": {
                "backup_count": 5,
                "auto_backup": True,
            },
            "ui": {
                "auto_save_selections": True,
                "show_tooltips": True,
                "column_layout": "auto",  # auto, single, double
            },
        }

    def _load_config(self) -> None:
        """Load configuration from file if it exists."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    # Merge with defaults, preserving structure
                    self._merge_config(self._config, file_config)
                    logger.info(f"Configuration loaded from {self.config_file}")
            else:
                # Save default config to file
                self.save_config()
                logger.info("Created default configuration file")
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")

    def _merge_config(self, default: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries.

        Args:
            default: Default configuration dictionary to update
            override: Override values from file
        """
        for key, value in override.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value

    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            # Create directory if it doesn't exist
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {self.config_file}")
        except OSError as e:
            logger.error(f"Error saving configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'app.window.width')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        try:
            value = self._config
            for part in key.split("."):
                value = value[part]
            return value
        except (KeyError, TypeError):
            logger.warning(f"Configuration key '{key}' not found, using default: {default}")
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'app.window.width')
            value: Value to set
        """
        try:
            config_part = self._config
            keys = key.split(".")

            # Navigate to the parent of the target key
            for part in keys[:-1]:
                if part not in config_part:
                    config_part[part] = {}
                config_part = config_part[part]

            # Set the value
            config_part[keys[-1]] = value
            logger.debug(f"Configuration '{key}' set to: {value}")
        except (KeyError, TypeError) as e:
            logger.error(f"Error setting configuration '{key}': {e}")

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section.

        Args:
            section: Section name

        Returns:
            Configuration section dictionary
        """
        return self.get(section, {})

    def update_section(self, section: str, values: Dict[str, Any]) -> None:
        """Update entire configuration section.

        Args:
            section: Section name
            values: Dictionary of values to update
        """
        current_section = self.get_section(section)
        current_section.update(values)
        self.set(section, current_section)

    @property
    def app_name(self) -> str:
        """Get application name."""
        return self.get("app.name", "Windows Package Manager")

    @property
    def app_version(self) -> str:
        """Get application version."""
        return self.get("app.version", "1.0.0")

    @property
    def window_size(self) -> tuple[int, int]:
        """Get window size as (width, height)."""
        return (self.get("app.window.width", 800), self.get("app.window.height", 600))

    @property
    def winget_timeout(self) -> int:
        """Get winget command timeout in seconds."""
        return self.get("winget.timeout", 300)

    @property
    def retry_attempts(self) -> int:
        """Get number of retry attempts for failed installations."""
        return self.get("winget.retry_attempts", 3)


# Global configuration instance
config = Config()
