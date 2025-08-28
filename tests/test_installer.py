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
    @patch('core.installer.WingetManager')
    def test_install_packages_success(self, mock_winget):
        mock_instance = mock_winget.return_value
        mock_instance.install_package.return_value = {'success': True, 'package_id': 'id1'}
        
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

    @patch('core.installer.WingetManager')
    def test_install_packages_admin_required(self, mock_winget):
        mock_instance = mock_winget.return_value
        mock_instance.install_package.side_effect = AdminPrivilegesRequiredError("Admin required")
        
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
        self.assertTrue(call_args[1]['skipped'])

    @patch('core.installer.WingetManager')
    def test_install_packages_package_not_found(self, mock_winget):
        mock_instance = mock_winget.return_value
        mock_instance.install_package.side_effect = PackageNotFoundError("id1")
        
        installer = Installer()
        callback = MagicMock()
        thread = installer.install_packages(['id1'], callback)
        thread.join(timeout=5)
        
        callback.assert_called_once()
        call_args = callback.call_args[0]
        self.assertEqual(call_args[0], 'id1')
        self.assertFalse(call_args[1]['success'])
        self.assertEqual(call_args[1]['error_type'], 'not_found')
        self.assertTrue(call_args[1]['skipped'])

    @patch('core.installer.WingetManager')
    def test_install_packages_execution_error(self, mock_winget):
        mock_instance = mock_winget.return_value
        mock_instance.install_package.side_effect = WingetExecutionError("Command failed")
        
        installer = Installer()
        callback = MagicMock()
        thread = installer.install_packages(['id1'], callback)
        thread.join(timeout=5)
        
        callback.assert_called_once()
        call_args = callback.call_args[0]
        self.assertEqual(call_args[0], 'id1')
        self.assertFalse(call_args[1]['success'])
        self.assertEqual(call_args[1]['error_type'], 'WingetExecutionError')

    @patch('core.installer.WingetManager')
    def test_install_packages_stop_on_first_failure(self, mock_winget):
        mock_instance = mock_winget.return_value
        mock_instance.install_package.side_effect = InstallationFailedError("id1", "Installation failed")
        
        installer = Installer()
        callback = MagicMock()
        thread = installer.install_packages(['id1', 'id2'], callback, stop_on_first_failure=True)
        thread.join(timeout=5)
        
        # Should only call callback once (for the failed package)
        callback.assert_called_once()
        
        # Should only try to install the first package
        mock_instance.install_package.assert_called_once()

    def test_install_packages_empty_list(self):
        installer = Installer()
        thread = installer.install_packages([])
        thread.join(timeout=1)
        
        # Should complete immediately
        self.assertFalse(thread.is_alive())

    @patch('core.installer.WingetManager')
    def test_install_packages_already_installing(self, mock_winget):
        mock_instance = mock_winget.return_value
        mock_instance.install_package.return_value = {'success': True}
        
        installer = Installer()
        
        # Start first installation
        thread1 = installer.install_packages(['id1'])
        
        # Try to start second installation while first is running
        with self.assertRaises(RuntimeError):
            installer.install_packages(['id2'])
        
        thread1.join(timeout=5)

    def test_progress_tracking(self):
        installer = Installer()
        progress_updates = []
        
        def progress_callback(progress):
            progress_updates.append(progress.get_summary())
        
        with patch('core.installer.WingetManager') as mock_winget:
            mock_instance = mock_winget.return_value
            mock_instance.install_package.return_value = {'success': True}
            
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

    def test_wait_for_completion(self):
        installer = Installer()
        
        with patch('core.installer.WingetManager') as mock_winget:
            mock_instance = mock_winget.return_value
            mock_instance.install_package.return_value = {'success': True}
            
            thread = installer.install_packages(['id1'])
            completed = installer.wait_for_completion(timeout=5)
            
            self.assertTrue(completed)

    def test_get_installation_summary(self):
        installer = Installer()
        
        with patch('core.installer.WingetManager') as mock_winget:
            mock_instance = mock_winget.return_value
            mock_instance.install_package.return_value = {'success': True}
            
            thread = installer.install_packages(['id1', 'id2'])
            thread.join(timeout=5)
            
            summary = installer.get_installation_summary()
            self.assertIsNotNone(summary)
            self.assertEqual(summary['total'], 2)
            self.assertEqual(summary['successful'], 2)

    def test_is_installing_property(self):
        installer = Installer()
        self.assertFalse(installer.is_installing)
        
        with patch('core.installer.WingetManager') as mock_winget:
            mock_instance = mock_winget.return_value
            mock_instance.install_package.return_value = {'success': True}
            
            thread = installer.install_packages(['id1'])
            # Might be True or False depending on timing, but should not error
            installer.is_installing  # Just test the property access
            thread.join(timeout=5)
            self.assertFalse(installer.is_installing)

if __name__ == '__main__':
    unittest.main()
