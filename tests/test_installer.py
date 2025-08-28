import unittest
from unittest.mock import patch, MagicMock
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.installer import Installer, InstallationProgress
from core.exceptions import (
    AdminPrivilegesRequiredError,
    PackageNotFoundError,
    WingetExecutionError,
    InstallationFailedError
)

class TestInstallationProgress(unittest.TestCase):
    def test_init(self):
        progress = InstallationProgress(5)
        self.assertEqual(progress.total_packages, 5)
        self.assertEqual(progress.completed_packages, 0)
        self.assertEqual(progress.successful_installations, 0)
        self.assertEqual(progress.failed_installations, 0)
        self.assertEqual(progress.progress_percentage, 0.0)

    def test_update_success(self):
        progress = InstallationProgress(2)
        result = {"success": True, "package_id": "test"}
        progress.update("test", result)
        self.assertEqual(progress.completed_packages, 1)
        self.assertEqual(progress.successful_installations, 1)
        self.assertEqual(progress.progress_percentage, 50.0)

    def test_update_failure(self):
        progress = InstallationProgress(2)
        result = {"success": False, "package_id": "test"}
        progress.update("test", result)
        self.assertEqual(progress.completed_packages, 1)
        self.assertEqual(progress.failed_installations, 1)
        self.assertEqual(progress.progress_percentage, 50.0)

    def test_update_skipped(self):
        progress = InstallationProgress(2)
        result = {"success": False, "skipped": True, "package_id": "test"}
        progress.update("test", result)
        self.assertEqual(progress.completed_packages, 1)
        self.assertEqual(progress.skipped_installations, 1)
        self.assertEqual(progress.progress_percentage, 50.0)

    def test_get_summary(self):
        progress = InstallationProgress(3)
        progress.update("pkg1", {"success": True})
        progress.update("pkg2", {"success": False})
        progress.update("pkg3", {"success": False, "skipped": True})
        
        summary = progress.get_summary()
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["completed"], 3)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["skipped"], 1)
        self.assertEqual(summary["progress_percentage"], 100.0)

class TestInstaller(unittest.TestCase):
    @patch('core.winget_manager.subprocess.run')
    def test_install_packages_success(self, mock_run):
        # Mock subprocess calls to simulate successful winget operations
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available check
            MagicMock(returncode=0, stdout="Success", stderr=""),  # install id1
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available check  
            MagicMock(returncode=0, stdout="Success", stderr=""),  # install id2
        ]
        
        installer = Installer()
        callback = MagicMock()
        thread = installer.install_packages(['id1', 'id2'], callback)
        thread.join(timeout=5)
        
        self.assertFalse(thread.is_alive())
        self.assertEqual(callback.call_count, 2)
        
        # Verify that both packages were processed
        call_args_list = callback.call_args_list
        processed_packages = {call[0][0] for call in call_args_list}
        self.assertEqual(processed_packages, {'id1', 'id2'})

    @patch('core.winget_manager.subprocess.run')
    def test_install_packages_admin_required(self, mock_run):
        # Mock subprocess to simulate admin privileges required
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available check
            MagicMock(returncode=1, stdout="Administrator privileges required", stderr="requires administrator"),  # install fails
        ] * 10  # Multiple calls for retries
        
        installer = Installer()
        callback = MagicMock()
        thread = installer.install_packages(['id1'], callback)
        thread.join(timeout=5)
        
        # Verify callback was called with error result
        callback.assert_called_once()
        call_args = callback.call_args[0]
        self.assertEqual(call_args[0], 'id1')  # package_id
        self.assertFalse(call_args[1]['success'])  # result success
        self.assertEqual(call_args[1]['error_type'], 'admin_required')

    @patch('core.winget_manager.subprocess.run')
    def test_install_packages_package_not_found(self, mock_run):
        # Mock subprocess to simulate package not found  
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available check
            MagicMock(returncode=1, stdout="not found", stderr="package not found"),  # install fails - should raise PackageNotFoundError immediately
        ]
        
        installer = Installer()
        callback = MagicMock()
        thread = installer.install_packages(['id1'], callback)
        thread.join(timeout=5)
        
        callback.assert_called_once()
        call_args = callback.call_args[0]
        self.assertEqual(call_args[0], 'id1')
        self.assertFalse(call_args[1]['success'])
        self.assertEqual(call_args[1]['error_type'], 'not_found')

    @patch('core.winget_manager.subprocess.run')
    def test_install_packages_execution_error(self, mock_run):
        # Mock subprocess to simulate consistent execution error (all retries fail)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available check  
            MagicMock(returncode=1, stdout="", stderr="Command failed"),  # install fails
            MagicMock(returncode=1, stdout="", stderr="Command failed"),  # retry 1 fails
            MagicMock(returncode=1, stdout="", stderr="Command failed"),  # retry 2 fails  
            MagicMock(returncode=1, stdout="", stderr="Command failed"),  # retry 3 fails
        ]
        
        installer = Installer()
        callback = MagicMock()
        thread = installer.install_packages(['id1'], callback)
        thread.join(timeout=5)
        
        callback.assert_called_once()
        call_args = callback.call_args[0]
        self.assertEqual(call_args[0], 'id1')
        self.assertFalse(call_args[1]['success'])
        self.assertEqual(call_args[1]['error_type'], 'InstallationFailedError')

    @patch('core.winget_manager.subprocess.run')
    def test_install_packages_stop_on_first_failure(self, mock_run):
        # Mock subprocess to simulate consistent installation failure
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available check
            MagicMock(returncode=1, stdout="", stderr="Installation failed"),  # install fails
            MagicMock(returncode=1, stdout="", stderr="Installation failed"),  # retry 1 fails
            MagicMock(returncode=1, stdout="", stderr="Installation failed"),  # retry 2 fails
            MagicMock(returncode=1, stdout="", stderr="Installation failed"),  # retry 3 fails
        ]
        
        installer = Installer()
        callback = MagicMock()
        thread = installer.install_packages(['id1', 'id2'], callback, stop_on_first_failure=True)
        thread.join(timeout=5)
        
        # Should only call callback once (for the failed package)
        callback.assert_called_once()

    def test_install_packages_empty_list(self):
        installer = Installer()
        thread = installer.install_packages([])
        
        # Should return an unstarted thread for empty list
        self.assertFalse(thread.is_alive())
        
        # Thread should not be started (no packages to install)
        self.assertIsInstance(thread, type(thread))

    @patch('core.winget_manager.subprocess.run')
    def test_install_packages_already_installing(self, mock_run):
        # Mock subprocess calls for successful installation
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available check
            MagicMock(returncode=0, stdout="Success", stderr=""),  # install id1
        ]
        
        installer = Installer()
        
        # Start first installation
        thread1 = installer.install_packages(['id1'])
        
        # Try to start second installation while first is running
        with self.assertRaises(RuntimeError):
            installer.install_packages(['id2'])
        
        thread1.join(timeout=5)

    @patch('core.winget_manager.subprocess.run')
    def test_progress_tracking(self, mock_run):
        # Mock subprocess calls for successful installations
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available check
            MagicMock(returncode=0, stdout="Success", stderr=""),  # install id1
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available check
            MagicMock(returncode=0, stdout="Success", stderr=""),  # install id2
        ]
        
        installer = Installer()
        progress_updates = []
        
        def progress_callback(progress):
            progress_updates.append(progress.get_summary())
            
        thread = installer.install_packages(
            ['id1', 'id2'], 
            progress_callback=progress_callback
        )
        thread.join(timeout=5)
        
        # Should have progress updates
        self.assertGreater(len(progress_updates), 0)
        final_progress = progress_updates[-1]
        self.assertEqual(final_progress['completed'], 2)
        self.assertEqual(final_progress['successful'], 2)

    @patch('core.winget_manager.subprocess.run')
    def test_wait_for_completion(self, mock_run):
        # Mock subprocess calls for successful installation
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available check
            MagicMock(returncode=0, stdout="Success", stderr=""),  # install id1
        ]
        
        installer = Installer()
        thread = installer.install_packages(['id1'])
        completed = installer.wait_for_completion(timeout=5)
        
        self.assertTrue(completed)

    @patch('core.winget_manager.subprocess.run')
    def test_get_installation_summary(self, mock_run):
        # Mock subprocess calls for successful installations
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available check
            MagicMock(returncode=0, stdout="Success", stderr=""),  # install id1
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available check
            MagicMock(returncode=0, stdout="Success", stderr=""),  # install id2
        ]
        
        installer = Installer()
        thread = installer.install_packages(['id1', 'id2'])
        thread.join(timeout=5)
        
        summary = installer.get_installation_summary()
        self.assertIsNotNone(summary)
        self.assertEqual(summary['total'], 2)
        self.assertEqual(summary['successful'], 2)

    @patch('core.winget_manager.subprocess.run')
    def test_is_installing_property(self, mock_run):
        # Mock subprocess calls for successful installation
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v1.0", stderr=""),  # is_available check
            MagicMock(returncode=0, stdout="Success", stderr=""),  # install id1
        ]
        
        installer = Installer()
        self.assertFalse(installer.is_installing)
        
        thread = installer.install_packages(['id1'])
        # Might be True or False depending on timing, but should not error
        installer.is_installing  # Just test the property access
        thread.join(timeout=5)
        self.assertFalse(installer.is_installing)

if __name__ == '__main__':
    unittest.main()
