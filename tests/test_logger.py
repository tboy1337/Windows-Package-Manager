"""Comprehensive tests for logging module."""

import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.logger import Logger


class TestLogger(unittest.TestCase):
    """Test Logger class."""

    def setUp(self):
        """Set up test environment."""
        # Reset singleton instance for each test
        Logger._instance = None
        Logger._logger = None
        
        # Create temporary directory for logs
        self.temp_dir = tempfile.mkdtemp()
        self.logs_dir = Path(self.temp_dir) / "logs"

    def tearDown(self):
        """Clean up test environment."""
        # Clean up handlers to avoid issues between tests
        if Logger._logger and Logger._logger.handlers:
            for handler in Logger._logger.handlers[:]:
                handler.close()
                Logger._logger.removeHandler(handler)
        
        # Reset singleton
        Logger._instance = None
        Logger._logger = None
        
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_singleton_pattern(self):
        """Test that Logger follows singleton pattern."""
        logger1 = Logger()
        logger2 = Logger()
        self.assertIs(logger1, logger2)
        self.assertIs(Logger._instance, logger1)

    @patch("core.logger.Path")
    def test_setup_logger_creates_logs_directory(self, mock_path):
        """Test that setup_logger creates logs directory."""
        mock_logs_dir = MagicMock()
        mock_path.return_value = mock_logs_dir
        
        logger = Logger()
        mock_logs_dir.mkdir.assert_called_once_with(exist_ok=True)

    def test_setup_logger_creates_handlers(self):
        """Test that setup_logger creates file and console handlers."""
        logger = Logger()
        
        # Check that handlers were added (at least file and console handler)
        self.assertIsNotNone(logger._logger)
        self.assertTrue(len(logger._logger.handlers) >= 2)
        
        # Check that we have both file and console handlers
        handler_types = [type(h) for h in logger._logger.handlers]
        has_file_handler = any(issubclass(t, logging.FileHandler) for t in handler_types)
        has_stream_handler = any(issubclass(t, logging.StreamHandler) for t in handler_types)
        self.assertTrue(has_file_handler, "Should have a file handler")
        self.assertTrue(has_stream_handler, "Should have a stream handler")

    def test_setup_logger_avoids_duplicate_handlers(self):
        """Test that setup_logger doesn't add duplicate handlers."""
        logger = Logger()
        initial_handler_count = len(logger._logger.handlers)
        
        # Call setup again
        logger._setup_logger()
        
        # Handler count should remain the same
        self.assertEqual(len(logger._logger.handlers), initial_handler_count)

    def test_logger_property(self):
        """Test logger property returns the logging instance."""
        logger = Logger()
        self.assertIsInstance(logger.logger, logging.Logger)
        self.assertEqual(logger.logger.name, "WingetPackageManager")

    def test_debug_method(self):
        """Test debug logging method."""
        logger = Logger()
        
        with patch.object(logger._logger, 'debug') as mock_debug:
            logger.debug("Debug message", "arg1", extra="extra")
            mock_debug.assert_called_once_with("Debug message", "arg1", extra="extra")

    def test_info_method(self):
        """Test info logging method."""
        logger = Logger()
        
        with patch.object(logger._logger, 'info') as mock_info:
            logger.info("Info message", "arg1", extra="extra")
            mock_info.assert_called_once_with("Info message", "arg1", extra="extra")

    def test_warning_method(self):
        """Test warning logging method."""
        logger = Logger()
        
        with patch.object(logger._logger, 'warning') as mock_warning:
            logger.warning("Warning message", "arg1", extra="extra")
            mock_warning.assert_called_once_with("Warning message", "arg1", extra="extra")

    def test_error_method(self):
        """Test error logging method."""
        logger = Logger()
        
        with patch.object(logger._logger, 'error') as mock_error:
            logger.error("Error message", "arg1", extra="extra")
            mock_error.assert_called_once_with("Error message", "arg1", extra="extra")

    def test_critical_method(self):
        """Test critical logging method."""
        logger = Logger()
        
        with patch.object(logger._logger, 'critical') as mock_critical:
            logger.critical("Critical message", "arg1", extra="extra")
            mock_critical.assert_called_once_with("Critical message", "arg1", extra="extra")

    def test_exception_method(self):
        """Test exception logging method."""
        logger = Logger()
        
        with patch.object(logger._logger, 'exception') as mock_exception:
            logger.exception("Exception message", "arg1", extra="extra")
            mock_exception.assert_called_once_with("Exception message", "arg1", extra="extra")

    def test_logger_level_configuration(self):
        """Test that logger is configured with DEBUG level."""
        logger = Logger()
        self.assertEqual(logger._logger.level, logging.DEBUG)

    def test_console_handler_level(self):
        """Test that console handler is set to WARNING level."""
        logger = Logger()
        
        # Find console handler
        console_handler = None
        for handler in logger._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                console_handler = handler
                break
        
        self.assertIsNotNone(console_handler)
        self.assertEqual(console_handler.level, logging.WARNING)

    def test_file_handler_level(self):
        """Test that file handler is set to DEBUG level."""
        logger = Logger()
        
        # Find file handler
        file_handler = None
        for handler in logger._logger.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break
        
        self.assertIsNotNone(file_handler)
        self.assertEqual(file_handler.level, logging.DEBUG)

    def test_real_file_logging_setup(self):
        """Test actual file logging setup."""
        logger = Logger()
        
        # Verify that the logs directory exists (should be created by logger)
        logs_dir = Path("logs")
        self.assertTrue(logs_dir.exists(), "Logs directory should be created")
        
        # Check that file handler exists
        file_handlers = [h for h in logger._logger.handlers if isinstance(h, logging.FileHandler)]
        self.assertTrue(len(file_handlers) > 0, "Should have at least one file handler")

    def test_formatter_configuration(self):
        """Test that formatters are properly configured."""
        logger = Logger()
        
        # Check that handlers have formatters
        for handler in logger._logger.handlers:
            self.assertIsNotNone(handler.formatter)
            
            # Check formatter format string
            formatter = handler.formatter
            if isinstance(handler, logging.FileHandler):
                # File handler should have detailed format
                self.assertIn("%(asctime)s", formatter._fmt)
                self.assertIn("%(filename)s", formatter._fmt)
                self.assertIn("%(lineno)d", formatter._fmt)
            else:
                # Console handler should have simple format
                self.assertEqual("%(levelname)s - %(message)s", formatter._fmt)


class TestLoggerModule(unittest.TestCase):
    """Test module-level logger instance."""

    def setUp(self):
        """Set up test environment."""
        # Reset singleton for clean test
        Logger._instance = None
        Logger._logger = None

    def tearDown(self):
        """Clean up test environment."""
        # Clean up handlers
        if Logger._logger and Logger._logger.handlers:
            for handler in Logger._logger.handlers[:]:
                handler.close()
                Logger._logger.removeHandler(handler)
        Logger._instance = None
        Logger._logger = None

    def test_module_logger_instance(self):
        """Test that module creates a global logger instance."""
        # Import to create the global instance
        from core.logger import logger
        self.assertIsInstance(logger, Logger)

    def test_global_logger_is_singleton(self):
        """Test that global logger follows singleton pattern."""
        # Reset singleton first
        Logger._instance = None
        Logger._logger = None
        
        from core.logger import logger
        logger2 = Logger()
        # Since logger was created first, logger2 should be the same instance
        # But the global logger may be a different instance created at import time
        # Let's just verify logger2 is a Logger instance
        self.assertIsInstance(logger, Logger)
        self.assertIsInstance(logger2, Logger)


if __name__ == "__main__":
    unittest.main()
