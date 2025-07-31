import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
from gui.main_window import MainWindow
import sys
import os
from core.winget_manager import WingetManager
from core.installer import Installer
from core.app_database import AppDatabase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.app = MainWindow()
        self.app.update()  # Process pending events

    def tearDown(self):
        self.app.db.conn.close()
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

    @patch('gui.main_window.json.load')
    def test_load_apps_error(self, mock_load):
        mock_load.side_effect = Exception("Test error")
        with patch('gui.main_window.messagebox.showerror') as mock_msg:
            apps = self.app.load_apps()
            self.assertEqual(apps, [])
            mock_msg.assert_called_once_with("Error", "Failed to load app catalog: Test error")

    @patch('gui.main_window.json.load')
    def test_load_categories_error(self, mock_load):
        mock_load.side_effect = Exception("Test error")
        with patch('gui.main_window.messagebox.showerror') as mock_msg:
            cats = self.app.load_categories()
            self.assertEqual(cats, [])
            mock_msg.assert_called_once_with("Error", "Failed to load categories: Test error")

    def test_select_all(self):
        # Assume there are categories and apps loaded
        self.app.notebook.select(0)  # Select first tab
        current_tab = self.app.notebook.tab(0, "text")
        cat_apps = [app for app in self.app.apps if app['category'] == current_tab]
        self.app.select_all()
        self.assertEqual(len(self.app.selected_packages), len(cat_apps))

    def test_deselect_all(self):
        self.app.notebook.select(0)
        current_tab = self.app.notebook.tab(0, "text")
        cat_apps = [app for app in self.app.apps if app['category'] == current_tab]
        for app in cat_apps:
            self.app.selected_packages.add(app['id'])
        self.app.deselect_all()
        self.assertEqual(len(self.app.selected_packages), 0)

    @patch.object(WingetManager, 'search_packages', return_value=[])
    def test_perform_search_no_query(self, mock_search):
        self.app.search_var.set("")
        self.app.perform_search()
        self.assertEqual(self.app.notebook.tab(self.app.search_results_frame, 'state'), 'hidden')

    @patch.object(WingetManager, 'search_packages', return_value=[])
    def test_perform_search_no_results(self, mock_search):
        self.app.search_var.set("nonexistent")
        self.app.perform_search()
        self.assertEqual(self.app.notebook.tab(self.app.search_results_frame, 'state'), 'normal')
        self.app.update()
        children = self.app.search_results_frame.winfo_children()
        self.assertEqual(len(children), 1)
        self.assertIn("No results found", children[0].cget("text"))

    @patch.object(WingetManager, 'search_packages', return_value=[{'name': 'TestApp', 'id': 'Test.ID'}])
    def test_perform_search_with_results(self, mock_search):
        self.app.search_var.set("test")
        self.app.perform_search()
        self.assertEqual(self.app.notebook.tab(self.app.search_results_frame, 'state'), 'normal')
        self.app.update()
        children = self.app.search_results_frame.winfo_children()
        self.assertGreater(len(children), 0)
        self.assertIn("TestApp", children[0].cget("text"))

    @patch.object(WingetManager, 'is_available', return_value=True)
    @patch.object(Installer, 'install_packages')
    def test_install_selected_success(self, mock_install, mock_avail):
        self.app.selected_packages = {'Test.ID'}
        self.app.install_selected()
        mock_install.assert_called_once()

    def test_install_selected_no_packages(self):
        self.app.selected_packages = set()
        with patch('gui.main_window.messagebox.showinfo') as mock_info:
            self.app.install_selected()
            mock_info.assert_called_once_with("Info", "No packages selected")

    def test_install_selected_no_winget(self):
        self.app.selected_packages = {'Test.ID'}
        with patch.object(WingetManager, 'is_available', return_value=False) as mock_avail:
            with patch('gui.main_window.messagebox.showerror') as mock_err:
                self.app.install_selected()
                mock_err.assert_called_once_with("Error", "Winget is not available. Please install it.")

    @patch.object(AppDatabase, 'save_profile')
    def test_save_profile(self, mock_save):
        with patch('gui.main_window.simpledialog.askstring', return_value="test_profile"):
            with patch('gui.main_window.messagebox.showinfo') as mock_info:
                self.app.save_profile()
                mock_info.assert_called_once_with("Info", "Profile saved")

    @patch.object(AppDatabase, 'get_all_profiles', return_value=[])
    def test_load_profile_no_profiles(self, mock_get):
        with patch('gui.main_window.messagebox.showinfo') as mock_info:
            self.app.load_profile()
            mock_info.assert_called_once_with("Info", "No profiles saved")

    @patch.object(AppDatabase, 'get_all_profiles', return_value=['test_profile'])
    @patch.object(AppDatabase, 'load_profile', return_value=['Test.ID'])
    def test_load_profile_success(self, mock_load, mock_get):
        with patch('gui.main_window.simpledialog.askstring', return_value="test_profile"):
            with patch('gui.main_window.messagebox.showinfo') as mock_info:
                self.app.load_profile()
                self.assertIn('Test.ID', self.app.selected_packages)
                mock_info.assert_called_once_with("Info", "Profile loaded")

    def test_export_script_no_packages(self):
        self.app.selected_packages = set()
        with patch('gui.main_window.messagebox.showinfo') as mock_info:
            self.app.export_script()
            mock_info.assert_called_once_with("Info", "No packages selected to export")

    @patch('gui.main_window.filedialog.asksaveasfilename', return_value="test.cmd")
    def test_export_script_success(self, mock_file):
        self.app.selected_packages = {'Test.ID'}
        with patch('builtins.open') as mock_open:
            with patch('gui.main_window.messagebox.showinfo') as mock_info:
                self.app.export_script()
                mock_open.assert_called_once_with("test.cmd", 'w')
                mock_info.assert_called_once_with("Info", "Script exported successfully")

    def test_perform_search_clear_previous(self):
        self.app.search_var.set("test")
        with patch.object(WingetManager, 'search_packages', return_value=[{'name': 'App1', 'id': 'ID1'}]):
            self.app.perform_search()
        self.app.update()
        self.assertGreater(len(self.app.search_results_frame.winfo_children()), 0)
        with patch.object(WingetManager, 'search_packages', return_value=[]):
            self.app.perform_search()
        self.app.update()
        children = self.app.search_results_frame.winfo_children()
        self.assertEqual(len(children), 1)
        self.assertIn("No results found", children[0].cget("text"))

import time
@patch.object(WingetManager, 'is_available', return_value=True)
@patch.object(Installer, 'install_packages')
def test_install_selected_callback(self, mock_install_pkg, mock_admin, mock_avail):
    self.app.selected_packages = {'Test.ID'}
    orig_install = self.app.installer.install_packages
    def wrapped_install(*args, **kwargs):
        return orig_install(*args, **kwargs)
    with patch.object(self.app.installer, 'install_packages', side_effect=wrapped_install) as mock_install:
        self.app.install_selected()
        thread = mock_install.return_value
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
    self.app.update()
    log_content = self.app.log_text.get('1.0', 'end')
    self.assertIn("Installation started...", log_content)
    self.assertIn("Test.ID: Success", log_content)

if __name__ == '__main__':
    unittest.main()
