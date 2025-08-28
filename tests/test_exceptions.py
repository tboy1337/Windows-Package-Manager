"""Comprehensive tests for custom exceptions module."""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.exceptions import (
    WingetPackageManagerError,
    WingetNotAvailableError,
    WingetExecutionError,
    AdminPrivilegesRequiredError,
    PackageNotFoundError,
    InstallationFailedError,
    DatabaseError,
    ConfigurationError,
    UIError,
    FileOperationError,
)


class TestWingetPackageManagerError(unittest.TestCase):
    """Test base exception class."""

    def test_init_with_message_only(self):
        """Test initialization with message only."""
        error = WingetPackageManagerError("Test error")
        self.assertEqual(error.message, "Test error")
        self.assertIsNone(error.error_code)
        self.assertEqual(str(error), "Test error")

    def test_init_with_message_and_code(self):
        """Test initialization with message and error code."""
        error = WingetPackageManagerError("Test error", 500)
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.error_code, 500)
        self.assertEqual(str(error), "Test error")


class TestWingetNotAvailableError(unittest.TestCase):
    """Test WingetNotAvailableError."""

    def test_default_message(self):
        """Test default message."""
        error = WingetNotAvailableError()
        self.assertEqual(error.message, "Winget is not available on this system")
        self.assertEqual(error.error_code, 1001)

    def test_custom_message(self):
        """Test custom message."""
        error = WingetNotAvailableError("Custom winget error")
        self.assertEqual(error.message, "Custom winget error")
        self.assertEqual(error.error_code, 1001)


class TestWingetExecutionError(unittest.TestCase):
    """Test WingetExecutionError."""

    def test_init_with_message_only(self):
        """Test initialization with message only."""
        error = WingetExecutionError("Execution failed")
        self.assertEqual(error.message, "Execution failed")
        self.assertEqual(error.error_code, 1002)
        self.assertIsNone(error.command)
        self.assertIsNone(error.return_code)

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        error = WingetExecutionError("Command failed", "winget search", 1)
        self.assertEqual(error.message, "Command failed")
        self.assertEqual(error.error_code, 1002)
        self.assertEqual(error.command, "winget search")
        self.assertEqual(error.return_code, 1)


class TestAdminPrivilegesRequiredError(unittest.TestCase):
    """Test AdminPrivilegesRequiredError."""

    def test_default_message(self):
        """Test default message."""
        error = AdminPrivilegesRequiredError()
        self.assertEqual(error.message, "Administrator privileges are required")
        self.assertEqual(error.error_code, 1003)

    def test_custom_message(self):
        """Test custom message."""
        error = AdminPrivilegesRequiredError("Need admin rights")
        self.assertEqual(error.message, "Need admin rights")
        self.assertEqual(error.error_code, 1003)


class TestPackageNotFoundError(unittest.TestCase):
    """Test PackageNotFoundError."""

    def test_init(self):
        """Test initialization."""
        error = PackageNotFoundError("test.package")
        self.assertEqual(error.message, "Package 'test.package' not found")
        self.assertEqual(error.error_code, 1004)
        self.assertEqual(error.package_id, "test.package")


class TestInstallationFailedError(unittest.TestCase):
    """Test InstallationFailedError."""

    def test_init(self):
        """Test initialization."""
        error = InstallationFailedError("test.package", "Network timeout")
        expected_message = "Installation of 'test.package' failed: Network timeout"
        self.assertEqual(error.message, expected_message)
        self.assertEqual(error.error_code, 1005)
        self.assertEqual(error.package_id, "test.package")
        self.assertEqual(error.reason, "Network timeout")


class TestDatabaseError(unittest.TestCase):
    """Test DatabaseError."""

    def test_init_with_message_only(self):
        """Test initialization with message only."""
        error = DatabaseError("DB connection failed")
        self.assertEqual(error.message, "DB connection failed")
        self.assertEqual(error.error_code, 1006)
        self.assertIsNone(error.operation)

    def test_init_with_operation(self):
        """Test initialization with operation."""
        error = DatabaseError("Operation failed", "INSERT")
        self.assertEqual(error.message, "Operation failed")
        self.assertEqual(error.error_code, 1006)
        self.assertEqual(error.operation, "INSERT")


class TestConfigurationError(unittest.TestCase):
    """Test ConfigurationError."""

    def test_init_with_message_only(self):
        """Test initialization with message only."""
        error = ConfigurationError("Invalid config")
        self.assertEqual(error.message, "Invalid config")
        self.assertEqual(error.error_code, 1007)
        self.assertIsNone(error.config_key)

    def test_init_with_config_key(self):
        """Test initialization with config key."""
        error = ConfigurationError("Key not found", "app.window.width")
        self.assertEqual(error.message, "Key not found")
        self.assertEqual(error.error_code, 1007)
        self.assertEqual(error.config_key, "app.window.width")


class TestUIError(unittest.TestCase):
    """Test UIError."""

    def test_init_with_message_only(self):
        """Test initialization with message only."""
        error = UIError("Widget creation failed")
        self.assertEqual(error.message, "Widget creation failed")
        self.assertEqual(error.error_code, 1008)
        self.assertIsNone(error.component)

    def test_init_with_component(self):
        """Test initialization with component."""
        error = UIError("Button click failed", "install_button")
        self.assertEqual(error.message, "Button click failed")
        self.assertEqual(error.error_code, 1008)
        self.assertEqual(error.component, "install_button")


class TestFileOperationError(unittest.TestCase):
    """Test FileOperationError."""

    def test_init_with_message_only(self):
        """Test initialization with message only."""
        error = FileOperationError("File not found")
        self.assertEqual(error.message, "File not found")
        self.assertEqual(error.error_code, 1009)
        self.assertIsNone(error.file_path)

    def test_init_with_file_path(self):
        """Test initialization with file path."""
        error = FileOperationError("Cannot read file", "/path/to/file.txt")
        self.assertEqual(error.message, "Cannot read file")
        self.assertEqual(error.error_code, 1009)
        self.assertEqual(error.file_path, "/path/to/file.txt")


if __name__ == "__main__":
    unittest.main()
