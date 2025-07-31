import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
from gui.main_window import MainWindow
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.app = MainWindow()
        self.app.update()  # Process pending events

    def tearDown(self):
        self.app.destroy()

    @patch('gui.main_window.json.load')
    def test_load_apps(self, mock_load):
        mock_load.return_value = [{'name': 'Test', 'id': 'Test.ID', 'category': 'Test'}]
        apps = self.app.load_apps()
        self.assertEqual(len(apps), 1)

    @patch('gui.main_window.json.load')
    def test_load_categories(self, mock_load):
        mock_load.return_value = {'categories': ['Test']}
        cats = self.app.load_categories()
        self.assertEqual(cats, ['Test'])

    def test_toggle_select(self):
        var = tk.BooleanVar(value=False)
        self.app.toggle_select('id1', var)
        self.assertNotIn('id1', self.app.selected_packages)
        var.set(True)
        self.app.toggle_select('id1', var)
        self.assertIn('id1', self.app.selected_packages)

    @patch.object(MainWindow, 'populate_category')
    def test_create_ui(self, mock_populate):
        self.app.create_ui()
        self.assertTrue(hasattr(self.app, 'notebook'))
        self.assertTrue(hasattr(self.app, 'search_results_frame'))

    # More tests for other methods can be added for higher coverage

if __name__ == '__main__':
    unittest.main()
