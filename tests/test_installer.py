import unittest
from unittest.mock import patch, MagicMock
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.installer import Installer

class TestInstaller(unittest.TestCase):
    @patch('core.installer.WingetManager')
    def test_install_packages(self, mock_winget):
        mock_instance = mock_winget.return_value
        mock_instance.install_package.return_value = {'success': True}
        installer = Installer()
        callback = MagicMock()
        thread = installer.install_packages(['id1', 'id2'], callback)
        thread.join(timeout=5)  # Wait for thread to finish
        self.assertFalse(thread.is_alive())
        callback.assert_any_call('id1', {'success': True})
        callback.assert_any_call('id2', {'success': True})
        self.assertEqual(callback.call_count, 2)

    @patch('core.installer.WingetManager')
    def test_install_packages_with_retry(self, mock_winget):
        mock_instance = mock_winget.return_value
        mock_instance.install_package.side_effect = [{'success': False}, {'success': False}, {'success': True}]
        installer = Installer()
        callback = MagicMock()
        thread = installer.install_packages(['id1'], callback)
        thread.join(timeout=5)
        callback.assert_called_once_with('id1', {'success': True})

    @patch('core.installer.WingetManager')
    def test_install_packages_retry_fail(self, mock_winget):
        mock_instance = mock_winget.return_value
        mock_instance.install_package.return_value = {'success': False}
        installer = Installer()
        callback = MagicMock()
        thread = installer.install_packages(['id1'], callback)
        thread.join(timeout=5)
        self.assertEqual(mock_instance.install_package.call_count, 3)
        callback.assert_called_once_with('id1', {'success': False})

    @patch('core.installer.WingetManager')
    def test_install_packages_admin_error_no_retry(self, mock_winget):
        mock_instance = mock_winget.return_value
        mock_instance.install_package.return_value = {'success': False, 'error': 'Administrator required'}
        installer = Installer()
        callback = MagicMock()
        thread = installer.install_packages(['id1'], callback)
        thread.join(timeout=5)
        self.assertEqual(mock_instance.install_package.call_count, 1)
        callback.assert_called_once_with('id1', {'success': False, 'error': 'Administrator required'})

if __name__ == '__main__':
    unittest.main()
