"""Additional tests to fill coverage gaps for 100% coverage."""

import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.installer import Installer, InstallationProgress
from core.winget_manager import WingetManager
from core.exceptions import (
    WingetNotAvailableError, 
    WingetExecutionError,
    PackageNotFoundError
)


class TestCoverageGaps(unittest.TestCase):
    """Test cases specifically to fill coverage gaps."""

    def test_installation_progress_zero_packages(self):
        """Test progress_percentage when total_packages is 0."""
        progress = InstallationProgress(0)
        # This should hit line 60: return 100.0
        self.assertEqual(progress.progress_percentage, 100.0)

    def test_installer_get_progress_initial_state(self):
        """Test get_progress when no installation has started."""
        installer = Installer()
        # This should hit line 101: return self._current_progress (None)
        self.assertIsNone(installer.get_progress())

    def test_installer_wait_for_completion_no_thread(self):
        """Test wait_for_completion when no installation thread exists."""
        installer = Installer()
        # This should hit line 253: return True
        self.assertTrue(installer.wait_for_completion())

    def test_installer_get_summary_no_progress(self):
        """Test get_installation_summary when no progress exists."""
        installer = Installer()
        # This should hit line 262: return None  
        self.assertIsNone(installer.get_installation_summary())

    @patch('core.winget_manager.subprocess.run')
    def test_winget_is_available_warning_log(self, mock_run):
        """Test is_available with failed return code (warning log)."""
        mock_run.return_value = MagicMock(returncode=1, stderr="Command not found")
        
        # This should hit line 46: logger.warning for failed winget check
        result = WingetManager.is_available()
        self.assertFalse(result)

    @patch('core.winget_manager.subprocess.run')
    def test_winget_is_available_timeout(self, mock_run):
        """Test is_available with timeout exception."""
        mock_run.side_effect = subprocess.TimeoutExpired(['winget', '--version'], 30)
        
        # This should hit lines 52-53: TimeoutExpired handling
        with self.assertRaises(WingetNotAvailableError):
            WingetManager.is_available()

    @patch('core.winget_manager.subprocess.run')
    def test_search_packages_winget_not_available(self, mock_run):
        """Test search_packages when winget is not available."""
        mock_run.return_value = MagicMock(returncode=1, stderr="Not found")
        
        # This should hit line 141: raise WingetNotAvailableError
        with self.assertRaises(WingetNotAvailableError):
            WingetManager.search_packages("test")

    @patch('core.winget_manager.subprocess.run') 
    def test_search_packages_timeout(self, mock_run):
        """Test search_packages with timeout."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available
            subprocess.TimeoutExpired(['winget', 'search'], 30)  # search timeout
        ]
        
        # This should hit lines 168-172: TimeoutExpired in search
        with self.assertRaises(WingetExecutionError):
            WingetManager.search_packages("test")

    @patch('core.winget_manager.subprocess.run')
    def test_search_packages_generic_exception(self, mock_run):
        """Test search_packages with generic exception."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available
            RuntimeError("Unexpected error")  # search fails
        ]
        
        # This should hit lines 176-177: generic exception handling
        with self.assertRaises(WingetExecutionError):
            WingetManager.search_packages("test")

    @patch('core.winget_manager.subprocess.run')
    def test_install_package_winget_not_available(self, mock_run):
        """Test install_package when winget becomes unavailable during install."""
        mock_run.return_value = MagicMock(returncode=1, stderr="Command not found")
        
        # This should hit line 206: WingetNotAvailableError re-raise
        with self.assertRaises(WingetNotAvailableError):
            WingetManager.install_package("test.package")

    @patch('core.winget_manager.subprocess.run')
    def test_install_package_permanent_error(self, mock_run):
        """Test install_package with permanent error (already installed)."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available
            MagicMock(returncode=1, stdout="package already installed", stderr="")
        ]
        
        # This should hit lines 293-296: permanent error detection
        result = WingetManager.install_package("test.package")
        self.assertFalse(result['success'])

    @patch('core.winget_manager.subprocess.run')
    def test_install_package_timeout_with_retry(self, mock_run):
        """Test install_package with timeout that gets retried."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available
            subprocess.TimeoutExpired(['winget', 'install'], 30),  # timeout
            MagicMock(returncode=0, stdout="Installed", stderr="")  # retry succeeds
        ]
        
        # This should hit lines 299-305: timeout handling with retry
        result = WingetManager.install_package("test.package")
        self.assertTrue(result['success'])

    @patch('core.winget_manager.subprocess.run')
    def test_install_package_timeout_all_retries_fail(self, mock_run):
        """Test install_package when all retries timeout."""
        timeouts = [subprocess.TimeoutExpired(['winget', 'install'], 30)] * 10
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available
        ] + timeouts
        
        # This should hit lines 304-305: final timeout exception
        with self.assertRaises(WingetExecutionError):
            WingetManager.install_package("test.package")

    @patch('core.winget_manager.subprocess.run')
    def test_installer_package_not_found_exception(self, mock_run):
        """Test installer handling PackageNotFoundError."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available
            MagicMock(returncode=1, stdout="not found", stderr="package not found")
        ]
        
        installer = Installer()
        callback = MagicMock()
        
        # This should hit lines 161-162: PackageNotFoundError handling
        thread = installer.install_packages(['test.package'], callback)
        thread.join(timeout=2)
        
        # Verify the package not found error was handled
        callback.assert_called_once()
        call_args = callback.call_args[0]
        self.assertEqual(call_args[1]['error_type'], 'not_found')

    @patch('core.winget_manager.subprocess.run')
    def test_installer_generic_exception_stop_on_failure(self, mock_run):
        """Test installer with generic exception and stop_on_first_failure."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available
            RuntimeError("Unexpected error")  # causes generic exception
        ]
        
        installer = Installer()  
        callback = MagicMock()
        
        # This should hit lines 191-205: generic Exception handling with stop_on_first_failure
        thread = installer.install_packages(
            ['test.package1', 'test.package2'], 
            callback, 
            stop_on_first_failure=True
        )
        thread.join(timeout=2)
        
        # Should have stopped after first failure
        callback.assert_called_once()
        call_args = callback.call_args[0]
        self.assertEqual(call_args[1]['error_type'], 'unexpected_error')


if __name__ == '__main__':
    unittest.main()
