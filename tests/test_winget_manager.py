import unittest
from unittest.mock import patch, MagicMock
from core.winget_manager import WingetManager
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestWingetManager(unittest.TestCase):
    def test_is_available_true(self):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            self.assertTrue(WingetManager.is_available())

    def test_is_available_false(self):
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError
            self.assertFalse(WingetManager.is_available())

    def test_is_admin_true(self):
        with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
            self.assertTrue(WingetManager.is_admin())

    def test_is_admin_false(self):
        with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=0):
            self.assertFalse(WingetManager.is_admin())

    def test_is_admin_exception(self):
        with patch('ctypes.windll.shell32.IsUserAnAdmin', side_effect=Exception):
            self.assertFalse(WingetManager.is_admin())

    def test_parse_search_output_empty(self):
        self.assertEqual(WingetManager.parse_search_output(''), [])

    def test_parse_search_output_no_header(self):
        output = "Random text\nNo header"
        self.assertEqual(WingetManager.parse_search_output(output), [])

    def test_parse_search_output_with_data(self):
        output = """Name                               Id                           Version            Source
----                               --                           -------            ------
Google Chrome                      Google.Chrome                127.0.6533.73      winget
Firefox                            Mozilla.Firefox              128.0.3            winget"""
        parsed = WingetManager.parse_search_output(output)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]['name'], 'Google Chrome')
        self.assertEqual(parsed[0]['id'], 'Google.Chrome')
        self.assertEqual(parsed[0]['version'], '127.0.6533.73')
        self.assertEqual(parsed[0]['source'], 'winget')

    def test_parse_search_output_with_empty_line(self):
        output = """Name                               Id                           Version            Source
----                               --                           -------            ------
Google Chrome                      Google.Chrome                127.0.6533.73      winget

Firefox                            Mozilla.Firefox              128.0.3            winget"""
        parsed = WingetManager.parse_search_output(output)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]['name'], 'Google Chrome')
        self.assertEqual(parsed[1]['name'], 'Firefox')

    @patch('subprocess.run')
    def test_search_packages_success(self, mock_run):
        sample_output = """Name      Id         Version Source\n--------- --         ------- ------\nTest App  Test.ID    1.0     winget\n"""
        mock_run.return_value = MagicMock(returncode=0, stdout=sample_output)
        result = WingetManager.search_packages('test')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Test App')
        self.assertEqual(result[0]['id'], 'Test.ID')
        self.assertEqual(result[0]['version'], '1.0')
        self.assertEqual(result[0]['source'], 'winget')

    @patch('subprocess.run')
    def test_search_packages_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        result = WingetManager.search_packages('app')
        self.assertEqual(result, [])

    @patch('subprocess.run')
    def test_install_package_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="Installed", stderr="")
        result = WingetManager.install_package('App.ID')
        mock_run.assert_called_once_with(['winget', 'install', '--id', 'App.ID', '--exact', '--disable-interactivity', '--silent', '--accept-package-agreements', '--accept-source-agreements'], capture_output=True, text=True)
        self.assertTrue(result['success'])
        self.assertEqual(result['stdout'], "Installed")
        self.assertEqual(result['stderr'], "")

    @patch('subprocess.run')
    def test_install_package_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")
        result = WingetManager.install_package('App.ID')
        mock_run.assert_called_once_with(['winget', 'install', '--id', 'App.ID', '--exact', '--disable-interactivity', '--silent', '--accept-package-agreements', '--accept-source-agreements'], capture_output=True, text=True)
        self.assertFalse(result['success'])
        self.assertEqual(result['stderr'], "Error")

if __name__ == '__main__':
    unittest.main()
