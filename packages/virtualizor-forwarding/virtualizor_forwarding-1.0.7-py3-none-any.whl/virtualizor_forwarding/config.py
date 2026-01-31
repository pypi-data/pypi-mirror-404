"""
Configuration management for Virtualizor Forwarding Tool.

Handles loading, saving, and managing multi-host configurations.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

from .models import Config, HostProfile


class ConfigError(Exception):
    """Configuration related errors."""

    pass


class ConfigManager:
    """Manages application configuration with multiple host profiles."""

    DEFAULT_CONFIG_DIR = "~/.config/virtualizor-forwarding"
    CONFIG_FILENAME = "config.json"

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize ConfigManager.

        Args:
            config_path: Optional custom path to config file.
                        Defaults to ~/.config/virtualizor-forwarding/config.json
        """
        if config_path:
            self._config_path = Path(config_path).expanduser()
        else:
            self._config_path = (
                Path(self.DEFAULT_CONFIG_DIR).expanduser() / self.CONFIG_FILENAME
            )

        self._config: Optional[Config] = None

    @property
    def config_path(self) -> Path:
        """Get the configuration file path."""
        return self._config_path

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Config:
        """
        Load configuration from file.

        Returns:
            Config object with loaded data or empty config if file doesn't exist.

        Raises:
            ConfigError: If config file is corrupted or unreadable.
        """
        if not self._config_path.exists():
            self._config = Config()
            return self._config

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._config = Config.from_dict(data)
            return self._config
        except json.JSONDecodeError as e:
            raise ConfigError(
                f"Configuration file is corrupted: {e}\n"
                f"File: {self._config_path}\n"
                "Try removing the file or restoring from backup."
            )
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {e}")

    def save(self, config: Optional[Config] = None) -> None:
        """
        Save configuration to file.

        Args:
            config: Config object to save. Uses internal config if not provided.

        Raises:
            ConfigError: If save operation fails.
        """
        if config is not None:
            self._config = config

        if self._config is None:
            self._config = Config()

        try:
            self._ensure_config_dir()
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config.to_dict(), f, indent=2)
        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {e}")

    def add_host(self, name: str, profile: HostProfile) -> None:
        """
        Add new host profile.

        Args:
            name: Unique name for the host profile.
            profile: HostProfile object to add.

        Raises:
            ConfigError: If host with same name already exists.
        """
        if self._config is None:
            self.load()

        if name in self._config.hosts:
            raise ConfigError(f"Host profile '{name}' already exists.")

        self._config.hosts[name] = profile

        # Set as default if it's the first host
        if len(self._config.hosts) == 1:
            self._config.default_host = name

        self.save()

    def remove_host(self, name: str) -> None:
        """
        Remove host profile.

        Args:
            name: Name of the host profile to remove.

        Raises:
            ConfigError: If host doesn't exist.
        """
        if self._config is None:
            self.load()

        if name not in self._config.hosts:
            raise ConfigError(f"Host profile '{name}' does not exist.")

        del self._config.hosts[name]

        # Update default if removed host was default
        if self._config.default_host == name:
            if self._config.hosts:
                self._config.default_host = next(iter(self._config.hosts.keys()))
            else:
                self._config.default_host = None

        self.save()

    def get_host(self, name: str) -> HostProfile:
        """
        Get specific host profile.

        Args:
            name: Name of the host profile.

        Returns:
            HostProfile object.

        Raises:
            ConfigError: If host doesn't exist.
        """
        if self._config is None:
            self.load()

        if name not in self._config.hosts:
            raise ConfigError(
                f"Host profile '{name}' does not exist.\n"
                f"Available hosts: {', '.join(self._config.hosts.keys()) or 'none'}"
            )

        return self._config.hosts[name]

    def list_hosts(self) -> List[str]:
        """
        List all configured host names.

        Returns:
            List of host profile names.
        """
        if self._config is None:
            self.load()

        return list(self._config.hosts.keys())

    def set_default(self, name: str) -> None:
        """
        Set default host profile.

        Args:
            name: Name of the host profile to set as default.

        Raises:
            ConfigError: If host doesn't exist.
        """
        if self._config is None:
            self.load()

        if name not in self._config.hosts:
            raise ConfigError(f"Host profile '{name}' does not exist.")

        self._config.default_host = name
        self.save()

    def get_default(self) -> Optional[HostProfile]:
        """
        Get default host profile.

        Returns:
            Default HostProfile or None if not set.
        """
        if self._config is None:
            self.load()

        if not self._config.default_host:
            return None

        return self._config.hosts.get(self._config.default_host)

    def get_default_name(self) -> Optional[str]:
        """
        Get name of default host profile.

        Returns:
            Name of default host or None if not set.
        """
        if self._config is None:
            self.load()

        return self._config.default_host

    def has_hosts(self) -> bool:
        """Check if any hosts are configured."""
        if self._config is None:
            self.load()

        return len(self._config.hosts) > 0

    def get_all_hosts(self) -> dict[str, HostProfile]:
        """Get all host profiles."""
        if self._config is None:
            self.load()

        return self._config.hosts.copy()
