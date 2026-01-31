"""
Unit tests for configuration management.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path

from virtualizor_forwarding.config import ConfigManager, ConfigError
from virtualizor_forwarding.models import HostProfile, Config


class TestConfigManager:
    """Tests for ConfigManager class."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def temp_config_path(self, temp_config_dir):
        """Create temp config path without creating the file."""
        return os.path.join(temp_config_dir, "config.json")

    def test_init_default_path(self):
        """Test initialization with default path."""
        manager = ConfigManager()
        assert "virtualizor-forwarding" in str(manager.config_path)
        assert manager.config_path.name == "config.json"

    def test_init_custom_path(self, temp_config_path):
        """Test initialization with custom path."""
        manager = ConfigManager(config_path=temp_config_path)
        assert str(manager.config_path) == temp_config_path

    def test_load_nonexistent_file(self, temp_config_path):
        """Test loading when config file doesn't exist."""
        manager = ConfigManager(config_path=temp_config_path)
        config = manager.load()
        assert isinstance(config, Config)
        assert config.hosts == {}
        assert config.default_host is None

    def test_load_valid_config(self, temp_config_path):
        """Test loading valid config file."""
        # Write valid config
        config_data = {
            "hosts": {
                "prod": {
                    "name": "prod",
                    "api_url": "https://example.com:4083/index.php",
                    "api_key": "key",
                    "api_pass": "pass",
                }
            },
            "default_host": "prod",
            "version": "1.0",
        }
        with open(temp_config_path, "w") as f:
            json.dump(config_data, f)

        manager = ConfigManager(config_path=temp_config_path)
        config = manager.load()
        assert "prod" in config.hosts
        assert config.default_host == "prod"

    def test_load_corrupted_config(self, temp_config_path):
        """Test loading corrupted config file."""
        with open(temp_config_path, "w") as f:
            f.write("not valid json {{{")

        manager = ConfigManager(config_path=temp_config_path)
        with pytest.raises(ConfigError) as exc_info:
            manager.load()
        assert "corrupted" in str(exc_info.value).lower()

    def test_save_config(self, temp_config_path):
        """Test saving config."""
        manager = ConfigManager(config_path=temp_config_path)
        profile = HostProfile(
            name="test",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="pass",
        )
        config = Config(hosts={"test": profile}, default_host="test")
        manager.save(config)

        # Verify file was written
        assert os.path.exists(temp_config_path)
        with open(temp_config_path) as f:
            data = json.load(f)
        assert "test" in data["hosts"]

    def test_add_host(self, temp_config_path):
        """Test adding a host."""
        manager = ConfigManager(config_path=temp_config_path)
        profile = HostProfile.create(
            name="prod",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="password",
        )
        manager.add_host("prod", profile)

        config = manager.load()
        assert "prod" in config.hosts
        # First host should be set as default
        assert config.default_host == "prod"

    def test_add_host_duplicate(self, temp_config_path):
        """Test adding duplicate host raises error."""
        manager = ConfigManager(config_path=temp_config_path)
        profile = HostProfile.create(
            name="prod",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="password",
        )
        manager.add_host("prod", profile)

        with pytest.raises(ConfigError) as exc_info:
            manager.add_host("prod", profile)
        assert "already exists" in str(exc_info.value)

    def test_remove_host(self, temp_config_path):
        """Test removing a host."""
        manager = ConfigManager(config_path=temp_config_path)
        profile = HostProfile.create(
            name="prod",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="password",
        )
        manager.add_host("prod", profile)
        manager.remove_host("prod")

        config = manager.load()
        assert "prod" not in config.hosts

    def test_remove_nonexistent_host(self, temp_config_path):
        """Test removing nonexistent host raises error."""
        manager = ConfigManager(config_path=temp_config_path)
        manager.load()  # Initialize empty config
        with pytest.raises(ConfigError) as exc_info:
            manager.remove_host("nonexistent")
        assert "does not exist" in str(exc_info.value)

    def test_remove_default_host_updates_default(self, temp_config_path):
        """Test removing default host updates default to another host."""
        manager = ConfigManager(config_path=temp_config_path)
        profile1 = HostProfile.create(
            name="prod",
            api_url="https://prod.com:4083/index.php",
            api_key="key1",
            api_pass="pass1",
        )
        profile2 = HostProfile.create(
            name="staging",
            api_url="https://staging.com:4083/index.php",
            api_key="key2",
            api_pass="pass2",
        )
        manager.add_host("prod", profile1)
        manager.add_host("staging", profile2)
        manager.set_default("prod")

        manager.remove_host("prod")
        config = manager.load()
        assert config.default_host == "staging"

    def test_get_host(self, temp_config_path):
        """Test getting a specific host."""
        manager = ConfigManager(config_path=temp_config_path)
        profile = HostProfile.create(
            name="prod",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="password",
        )
        manager.add_host("prod", profile)

        retrieved = manager.get_host("prod")
        assert retrieved.name == "prod"
        assert retrieved.api_url == "https://example.com:4083/index.php"

    def test_get_nonexistent_host(self, temp_config_path):
        """Test getting nonexistent host raises error."""
        manager = ConfigManager(config_path=temp_config_path)
        manager.load()
        with pytest.raises(ConfigError) as exc_info:
            manager.get_host("nonexistent")
        assert "does not exist" in str(exc_info.value)

    def test_list_hosts(self, temp_config_path):
        """Test listing all hosts."""
        manager = ConfigManager(config_path=temp_config_path)
        profile1 = HostProfile.create(
            name="prod",
            api_url="https://prod.com:4083/index.php",
            api_key="key1",
            api_pass="pass1",
        )
        profile2 = HostProfile.create(
            name="staging",
            api_url="https://staging.com:4083/index.php",
            api_key="key2",
            api_pass="pass2",
        )
        manager.add_host("prod", profile1)
        manager.add_host("staging", profile2)

        hosts = manager.list_hosts()
        assert "prod" in hosts
        assert "staging" in hosts
        assert len(hosts) == 2

    def test_set_default(self, temp_config_path):
        """Test setting default host."""
        manager = ConfigManager(config_path=temp_config_path)
        profile1 = HostProfile.create(
            name="prod",
            api_url="https://prod.com:4083/index.php",
            api_key="key1",
            api_pass="pass1",
        )
        profile2 = HostProfile.create(
            name="staging",
            api_url="https://staging.com:4083/index.php",
            api_key="key2",
            api_pass="pass2",
        )
        manager.add_host("prod", profile1)
        manager.add_host("staging", profile2)

        manager.set_default("staging")
        assert manager.get_default_name() == "staging"

    def test_set_default_nonexistent(self, temp_config_path):
        """Test setting nonexistent host as default raises error."""
        manager = ConfigManager(config_path=temp_config_path)
        manager.load()
        with pytest.raises(ConfigError):
            manager.set_default("nonexistent")

    def test_get_default(self, temp_config_path):
        """Test getting default host profile."""
        manager = ConfigManager(config_path=temp_config_path)
        profile = HostProfile.create(
            name="prod",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="password",
        )
        manager.add_host("prod", profile)

        default = manager.get_default()
        assert default is not None
        assert default.name == "prod"

    def test_get_default_none(self, temp_config_path):
        """Test getting default when none set."""
        manager = ConfigManager(config_path=temp_config_path)
        manager.load()
        default = manager.get_default()
        assert default is None

    def test_has_hosts_true(self, temp_config_path):
        """Test has_hosts returns True when hosts exist."""
        manager = ConfigManager(config_path=temp_config_path)
        profile = HostProfile.create(
            name="prod",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="password",
        )
        manager.add_host("prod", profile)
        assert manager.has_hosts() is True

    def test_has_hosts_false(self, temp_config_path):
        """Test has_hosts returns False when no hosts."""
        manager = ConfigManager(config_path=temp_config_path)
        manager.load()
        assert manager.has_hosts() is False

    def test_get_all_hosts(self, temp_config_path):
        """Test getting all hosts."""
        manager = ConfigManager(config_path=temp_config_path)
        profile1 = HostProfile.create(
            name="prod",
            api_url="https://prod.com:4083/index.php",
            api_key="key1",
            api_pass="pass1",
        )
        profile2 = HostProfile.create(
            name="staging",
            api_url="https://staging.com:4083/index.php",
            api_key="key2",
            api_pass="pass2",
        )
        manager.add_host("prod", profile1)
        manager.add_host("staging", profile2)

        all_hosts = manager.get_all_hosts()
        assert len(all_hosts) == 2
        assert "prod" in all_hosts
        assert "staging" in all_hosts
