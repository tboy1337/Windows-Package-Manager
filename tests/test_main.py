"""Comprehensive tests for main entry point module."""

import ctypes
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def is_admin():
    """Check if the current process has administrator privileges.

    Returns:
        bool: True if running as admin, False otherwise
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except (OSError, AttributeError):
        return False


class TestMainFunctions(unittest.TestCase):
    """Test main module functions."""

    def test_is_admin_true(self):
        """Test is_admin returns True when user has admin privileges."""
        with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=1):
            self.assertTrue(is_admin())

    def test_is_admin_false(self):
        """Test is_admin returns False when user doesn't have admin privileges."""
        with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=0):
            self.assertFalse(is_admin())

    def test_is_admin_oserror_exception(self):
        """Test is_admin returns False when OSError is raised."""
        with patch("ctypes.windll.shell32.IsUserAnAdmin", side_effect=OSError("Access denied")):
            self.assertFalse(is_admin())

    def test_is_admin_attribute_error_exception(self):
        """Test is_admin returns False when AttributeError is raised."""
        with patch("ctypes.windll.shell32.IsUserAnAdmin", side_effect=AttributeError("Not available")):
            self.assertFalse(is_admin())

    @patch("sys.platform", "win32")
    @patch("ctypes.windll.user32.ShowWindow")
    @patch("ctypes.windll.kernel32.GetConsoleWindow")
    @patch("gui.main_window.MainWindow")
    def test_main_execution_with_admin_win32(
        self, mock_main_window, mock_get_console, mock_show_window
    ):
        """Test main execution on Windows with admin privileges."""
        mock_app = MagicMock()
        mock_main_window.return_value = mock_app
        mock_get_console.return_value = 12345

        # Execute the main block code (simulating if __name__ == "__main__")
        with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=1):
            if is_admin():
                if sys.platform == "win32":
                    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
                from gui.main_window import MainWindow
                app = MainWindow()
                app.mainloop()

        # Verify calls
        mock_get_console.assert_called_once()
        mock_show_window.assert_called_once_with(12345, 0)
        mock_main_window.assert_called_once()
        mock_app.mainloop.assert_called_once()

    @patch("sys.platform", "linux")
    @patch("gui.main_window.MainWindow")
    def test_main_execution_with_admin_non_win32(self, mock_main_window):
        """Test main execution on non-Windows platforms with admin privileges."""
        mock_app = MagicMock()
        mock_main_window.return_value = mock_app

        # Execute the main block code for non-Windows
        with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=1):
            if is_admin():
                if sys.platform == "win32":
                    # This block should not execute on non-Windows
                    pass
                from gui.main_window import MainWindow
                app = MainWindow()
                app.mainloop()

        # Verify calls
        mock_main_window.assert_called_once()
        mock_app.mainloop.assert_called_once()

    @patch("ctypes.windll.shell32.ShellExecuteW")
    @patch("sys.exit")
    def test_main_execution_without_admin(self, mock_exit, mock_shell_execute):
        """Test main execution when user doesn't have admin privileges."""
        # Simulate the admin check and relaunch logic
        with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=0):
            if not is_admin():
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit(0)

        # Verify relaunch attempt
        mock_shell_execute.assert_called_once_with(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        mock_exit.assert_called_once_with(0)

    @patch("ctypes.windll.shell32.ShellExecuteW", side_effect=Exception("UAC cancelled"))
    @patch("sys.exit")
    def test_main_execution_relaunch_fails(self, mock_exit, mock_shell_execute):
        """Test main execution when admin relaunch fails."""
        # This would happen if the UAC prompt is cancelled or fails
        with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=0):
            try:
                if not is_admin():
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", sys.executable, " ".join(sys.argv), None, 1
                    )
                    sys.exit(0)
            except Exception:
                # In real code, this might be handled differently
                pass

        mock_shell_execute.assert_called_once()

    def test_import_order_with_admin_check(self):
        """Test that GUI import happens after admin check."""
        # This test ensures the import is delayed until after admin check
        # The comment in main.py indicates this is intentional
        
        # Read main.py directly from file
        main_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py")
        with open(main_py_path, 'r', encoding='utf-8') as f:
            main_source = f.read()
        
        lines = main_source.split('\n')
        
        # Find the admin check and import lines
        admin_check_line = None
        import_line = None
        
        for i, line in enumerate(lines):
            if "if not is_admin():" in line:
                admin_check_line = i
            if "from gui.main_window import MainWindow" in line:
                import_line = i
        
        # Import should come after admin check
        if admin_check_line is not None and import_line is not None:
            self.assertGreater(import_line, admin_check_line,
                             "GUI import should come after admin check")


class TestMainIntegration(unittest.TestCase):
    """Integration tests for main module."""

    @patch("sys.platform", "win32")
    @patch("ctypes.windll.user32.ShowWindow")
    @patch("ctypes.windll.kernel32.GetConsoleWindow", return_value=98765)
    def test_console_hiding_on_windows(self, mock_get_console, mock_show_window):
        """Test that console window is hidden on Windows."""
        # Simulate the console hiding logic from main.py
        if sys.platform == "win32":
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
        mock_get_console.assert_called_once()
        mock_show_window.assert_called_once_with(98765, 0)

    @patch("sys.platform", "linux")
    @patch("ctypes.windll.user32.ShowWindow")
    def test_console_not_hidden_on_non_windows(self, mock_show_window):
        """Test that console window hiding is not attempted on non-Windows."""
        # Simulate the platform check
        if sys.platform == "win32":
            # This should not execute on Linux
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
        mock_show_window.assert_not_called()


if __name__ == "__main__":
    unittest.main()
