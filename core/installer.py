"""Installer module for handling package installations with retry logic."""

import threading
from typing import List, Callable, Dict
from .winget_manager import WingetManager


class Installer:
    """Handles package installation with retry logic and threading support."""

    def __init__(self) -> None:
        """Initialize the installer with a WingetManager instance."""
        self.winget = WingetManager()

    def install_packages(
        self, package_ids: List[str], callback: Callable[[str, Dict[str, any]], None] = None
    ) -> threading.Thread:
        """Install multiple packages in a background thread.

        Args:
            package_ids: List of package IDs to install
            callback: Optional callback function called for each package result

        Returns:
            Thread object handling the installation
        """

        def install_thread() -> None:
            for pkg_id in package_ids:
                attempts = 0
                max_attempts = 3
                while attempts < max_attempts:
                    result = self.winget.install_package(pkg_id)
                    if result["success"]:
                        break
                    attempts += 1
                    if "error" in result and "admin" in result["error"].lower():
                        break  # No retry for admin issues
                if callback:
                    callback(pkg_id, result)

        thread = threading.Thread(target=install_thread)
        thread.start()
        return thread
