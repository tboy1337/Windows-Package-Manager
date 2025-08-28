"""Main entry point for Windows Package Manager GUI application."""

import ctypes
import sys


def is_admin():
    """Check if the current process has administrator privileges.

    Returns:
        bool: True if running as admin, False otherwise
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except (OSError, AttributeError):
        return False


if not is_admin():
    # Relaunch as admin
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)

# Import after admin check to avoid issues
from gui.main_window import MainWindow  # pylint: disable=wrong-import-position

if sys.platform == "win32":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
