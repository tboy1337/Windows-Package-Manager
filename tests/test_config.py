"""Comprehensive tests for configuration management module."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import Config


class TestConfig(unittest.TestCase):
    """Test Configuration manager."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.json"
        
        # Mock the logger to avoid logging issues during tests
        self.logger_patcher = patch('core.config.logger')
        self.mock_logger = self.logger_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
        # Clean up temp files
        if self.config_file.exists():
            self.config_file.unlink()
        # Clean up temp directory and any subdirectories
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_with_default_config(self):
        """Test initialization with default config file."""
        config = Config(str(self.config_file))
        self.assertIsNotNone(config._config)
        self.assertEqual(config.get("app.name"), "Windows Package Manager")
        self.assertEqual(config.get("app.version"), "1.0.0")

    def test_init_with_existing_config_file(self):
        """Test initialization with existing config file."""
        # Create a config file with custom values
        custom_config = {
            "app": {"name": "Custom App", "version": "2.0.0"},
            "winget": {"timeout": 500}
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(custom_config, f)

        config = Config(str(self.config_file))
        self.assertEqual(config.get("app.name"), "Custom App")
        self.assertEqual(config.get("app.version"), "2.0.0")
        self.assertEqual(config.get("winget.timeout"), 500)
        # Default values should still be present for unspecified keys
        self.assertEqual(config.get("winget.retry_attempts"), 3)

    def test_init_with_corrupted_config_file(self):
        """Test initialization with corrupted JSON file."""
        # Create invalid JSON file
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        config = Config(str(self.config_file))
        # Should fall back to defaults
        self.assertEqual(config.get("app.name"), "Windows Package Manager")
        self.mock_logger.error.assert_called()

    @patch("builtins.open", mock_open())
    @patch("pathlib.Path.exists", return_value=True)
    def test_init_with_file_read_error(self, mock_exists):
        """Test initialization when file cannot be read."""
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            config = Config(str(self.config_file))
            # Should use defaults
            self.assertEqual(config.get("app.name"), "Windows Package Manager")
            self.mock_logger.error.assert_called()

    def test_load_default_config(self):
        """Test loading default configuration."""
        config = Config(str(self.config_file))
        default_config = config._load_default_config()
        
        self.assertIn("app", default_config)
        self.assertIn("winget", default_config)
        self.assertIn("logging", default_config)
        self.assertIn("database", default_config)
        self.assertIn("ui", default_config)
        
        # Check specific values
        self.assertEqual(default_config["app"]["name"], "Windows Package Manager")
        self.assertEqual(default_config["app"]["version"], "1.0.0")
        self.assertEqual(default_config["winget"]["timeout"], 300)
        self.assertTrue(default_config["winget"]["silent_install"])

    def test_merge_config_simple(self):
        """Test simple config merging."""
        config = Config(str(self.config_file))
        default = {"key1": "value1", "key2": "value2"}
        override = {"key2": "new_value", "key3": "value3"}
        
        config._merge_config(default, override)
        
        self.assertEqual(default["key1"], "value1")  # unchanged
        self.assertEqual(default["key2"], "new_value")  # overridden
        self.assertEqual(default["key3"], "value3")  # added

    def test_merge_config_nested(self):
        """Test nested config merging."""
        config = Config(str(self.config_file))
        default = {
            "section1": {
                "nested1": "value1",
                "nested2": "value2"
            }
        }
        override = {
            "section1": {
                "nested2": "new_value",
                "nested3": "value3"
            }
        }
        
        config._merge_config(default, override)
        
        self.assertEqual(default["section1"]["nested1"], "value1")  # unchanged
        self.assertEqual(default["section1"]["nested2"], "new_value")  # overridden
        self.assertEqual(default["section1"]["nested3"], "value3")  # added

    def test_save_config_success(self):
        """Test successful config saving."""
        config = Config(str(self.config_file))
        config.set("app.name", "Test App")
        
        config.save_config()
        
        self.assertTrue(self.config_file.exists())
        with open(self.config_file, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config["app"]["name"], "Test App")

    def test_save_config_directory_creation(self):
        """Test config saving with directory creation."""
        nested_config_file = Path(self.temp_dir) / "subdir" / "config.json"
        config = Config(str(nested_config_file))
        
        config.save_config()
        
        self.assertTrue(nested_config_file.exists())
        self.assertTrue(nested_config_file.parent.exists())

    @patch("builtins.open", mock_open())
    def test_save_config_error(self):
        """Test config saving error handling."""
        config = Config(str(self.config_file))
        
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            config.save_config()
            self.mock_logger.error.assert_called()

    def test_get_existing_key(self):
        """Test getting existing configuration value."""
        config = Config(str(self.config_file))
        value = config.get("app.window.width")
        self.assertEqual(value, 800)

    def test_get_nonexistent_key_with_default(self):
        """Test getting nonexistent key with default value."""
        config = Config(str(self.config_file))
        value = config.get("nonexistent.key", "default_value")
        self.assertEqual(value, "default_value")
        self.mock_logger.warning.assert_called()

    def test_get_nonexistent_key_without_default(self):
        """Test getting nonexistent key without default value."""
        config = Config(str(self.config_file))
        value = config.get("nonexistent.key")
        self.assertIsNone(value)
        self.mock_logger.warning.assert_called()

    def test_get_invalid_key_format(self):
        """Test getting value with invalid key format."""
        config = Config(str(self.config_file))
        # This should cause a TypeError when trying to access nested keys
        config._config = {"app": "not_a_dict"}
        value = config.get("app.window.width", "default")
        self.assertEqual(value, "default")
        self.mock_logger.warning.assert_called()

    def test_set_existing_key(self):
        """Test setting existing configuration value."""
        config = Config(str(self.config_file))
        config.set("app.window.width", 1200)
        self.assertEqual(config.get("app.window.width"), 1200)

    def test_set_new_key(self):
        """Test setting new configuration value."""
        config = Config(str(self.config_file))
        config.set("new.section.key", "new_value")
        self.assertEqual(config.get("new.section.key"), "new_value")

    def test_set_nested_key_creation(self):
        """Test creating nested sections when setting keys."""
        config = Config(str(self.config_file))
        config.set("deep.nested.section.key", "value")
        self.assertEqual(config.get("deep.nested.section.key"), "value")

    def test_set_invalid_key_format(self):
        """Test setting value with invalid key format."""
        config = Config(str(self.config_file))
        # Try to set a value where parent is not a dict
        config._config = {"parent": "not_a_dict"}
        
        config.set("parent.child", "value")
        # Should log an error and not crash
        self.mock_logger.error.assert_called()

    def test_get_section_existing(self):
        """Test getting existing configuration section."""
        config = Config(str(self.config_file))
        section = config.get_section("app")
        self.assertIsInstance(section, dict)
        self.assertIn("name", section)
        self.assertIn("version", section)

    def test_get_section_nonexistent(self):
        """Test getting nonexistent configuration section."""
        config = Config(str(self.config_file))
        section = config.get_section("nonexistent_section")
        self.assertEqual(section, {})

    def test_update_section(self):
        """Test updating configuration section."""
        config = Config(str(self.config_file))
        updates = {"new_key": "new_value", "window": {"width": 1000}}
        config.update_section("app", updates)
        
        self.assertEqual(config.get("app.new_key"), "new_value")
        self.assertEqual(config.get("app.window.width"), 1000)

    def test_properties(self):
        """Test configuration properties."""
        config = Config(str(self.config_file))
        
        # Test app_name property
        self.assertEqual(config.app_name, "Windows Package Manager")
        
        # Test app_version property
        self.assertEqual(config.app_version, "1.0.0")
        
        # Test window_size property
        width, height = config.window_size
        self.assertEqual(width, 800)
        self.assertEqual(height, 600)
        
        # Test winget_timeout property
        self.assertEqual(config.winget_timeout, 300)
        
        # Test retry_attempts property
        self.assertEqual(config.retry_attempts, 3)

    def test_properties_with_missing_values(self):
        """Test properties when config values are missing."""
        config = Config(str(self.config_file))
        config._config = {}  # Empty config
        
        # Properties should return defaults
        self.assertEqual(config.app_name, "Windows Package Manager")
        self.assertEqual(config.app_version, "1.0.0")
        self.assertEqual(config.window_size, (800, 600))
        self.assertEqual(config.winget_timeout, 300)
        self.assertEqual(config.retry_attempts, 3)


if __name__ == "__main__":
    unittest.main()
