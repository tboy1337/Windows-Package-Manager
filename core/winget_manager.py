"""Windows Package Manager (winget) interface module."""

import subprocess
import ctypes
from typing import List, Dict

from .config import config
from .exceptions import (
    WingetNotAvailableError,
    WingetExecutionError,
    AdminPrivilegesRequiredError,
)
from .logger import logger


class WingetManager:
    """Interface for Windows Package Manager (winget) operations."""

    @staticmethod
    def is_available() -> bool:
        """Check if winget is available on the system.

        Returns:
            True if winget is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["winget", "--version"], capture_output=True, text=True, check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    @staticmethod
    def is_admin() -> bool:
        """Check if the current process is running with administrator privileges.

        Returns:
            True if running as admin, False otherwise
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except (OSError, AttributeError):
            return False

    @staticmethod
    def parse_search_output(output: str) -> List[Dict[str, str]]:
        """Parse winget search command output into structured data.

        Args:
            output: Raw output from winget search command

        Returns:
            List of dictionaries containing package information
        """
        lines = output.splitlines()
        if not lines:
            return []
        # Find header
        header_index = next(
            (i for i, line in enumerate(lines) if "Name" in line and "Id" in line), -1
        )
        if header_index == -1:
            return []
        header = lines[header_index]
        # Find column starts
        name_end = header.find("Id")
        id_start = name_end
        id_end = header.find("Version", id_start)
        version_start = id_end
        version_end = header.find("Source", version_start) if "Source" in header else len(header)
        source_start = version_end
        # Parse lines after header and separator (usually --- line)
        data_lines = lines[header_index + 2 :]  # Skip header and separator
        packages = []
        for line in data_lines:
            if not line.strip():
                continue
            name = line[:name_end].strip()
            id_ = line[id_start:version_start].strip()
            version = (
                line[version_start:source_start].strip()
                if source_start > version_start
                else line[version_start:].strip()
            )
            source = line[source_start:].strip() if source_start < len(line) else ""
            if name and id_:
                packages.append({"name": name, "id": id_, "version": version, "source": source})
        return packages

    @staticmethod
    def search_packages(query: str = "") -> List[Dict[str, str]]:
        """Search for packages using winget.

        Args:
            query: Search query string

        Returns:
            List of matching packages
        """
        cmd = ["winget", "search"]
        if query:
            cmd.extend(["--query", query])
        cmd.append("--accept-source-agreements")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return WingetManager.parse_search_output(result.stdout)
        return []

    @staticmethod
    def install_package(package_id: str, silent: bool = True) -> Dict[str, any]:
        """Install a package using winget.

        Args:
            package_id: Package identifier to install
            silent: Whether to install silently

        Returns:
            Dictionary containing installation result information
        """
        cmd = ["winget", "install", "--id", package_id, "--exact", "--disable-interactivity"]
        if silent:
            cmd.extend(["--silent", "--accept-package-agreements", "--accept-source-agreements"])
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
