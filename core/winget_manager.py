"""Windows Package Manager (winget) interface module."""

import ctypes
import subprocess
import time
from typing import Dict, List, Optional

from .config import config
from .exceptions import (
    AdminPrivilegesRequiredError,
    InstallationFailedError,
    PackageNotFoundError,
    WingetExecutionError,
    WingetNotAvailableError,
)
from .logger import logger


class WingetManager:
    """Interface for Windows Package Manager (winget) operations."""

    @staticmethod
    def is_available() -> bool:
        """Check if winget is available on the system.

        Returns:
            True if winget is available, False otherwise

        Raises:
            WingetNotAvailableError: If winget is not found or not working
        """
        try:
            logger.debug("Checking winget availability...")
            result = subprocess.run(
                ["winget", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=config.winget_timeout,
            )

            is_available = result.returncode == 0
            if is_available:
                logger.info(
                    f"Winget is available. Version output: {result.stdout.strip()}"
                )
            else:
                logger.warning(
                    f"Winget check failed with return code {result.returncode}: {result.stderr}"
                )

            return is_available
        except subprocess.TimeoutExpired:
            logger.error("Winget availability check timed out")
            raise WingetNotAvailableError("Winget availability check timed out") from None
        except FileNotFoundError:
            logger.error("Winget executable not found")
            raise WingetNotAvailableError("Winget executable not found") from None
        except Exception as e:
            logger.error(f"Unexpected error checking winget availability: {e}")
            raise WingetNotAvailableError(f"Unexpected error: {e}") from e

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
        version_end = (
            header.find("Source", version_start) if "Source" in header else len(header)
        )
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
                packages.append(
                    {"name": name, "id": id_, "version": version, "source": source}
                )
        return packages

    @staticmethod
    def search_packages(query: str = "") -> List[Dict[str, str]]:
        """Search for packages using winget.

        Args:
            query: Search query string

        Returns:
            List of matching packages

        Raises:
            WingetNotAvailableError: If winget is not available
            WingetExecutionError: If search command fails
        """
        try:
            logger.debug(f"Searching packages with query: '{query}'")

            # Verify winget is available
            if not WingetManager.is_available():
                raise WingetNotAvailableError()

            cmd = ["winget", "search"]
            if query:
                cmd.extend(["--query", query])
            cmd.append("--accept-source-agreements")

            logger.debug(f"Executing command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=config.winget_timeout,
            )

            if result.returncode == 0:
                packages = WingetManager.parse_search_output(result.stdout)
                logger.info(f"Found {len(packages)} packages for query '{query}'")
                return packages
            else:
                error_msg = f"Search command failed with return code {result.returncode}: {result.stderr}"
                logger.error(error_msg)
                raise WingetExecutionError(error_msg, " ".join(cmd), result.returncode)

        except subprocess.TimeoutExpired:
            error_msg = (
                f"Search command timed out after {config.winget_timeout} seconds"
            )
            logger.error(error_msg)
            raise WingetExecutionError(error_msg, " ".join(cmd))
        except Exception as e:
            if isinstance(e, (WingetNotAvailableError, WingetExecutionError)):
                raise
            logger.error(f"Unexpected error during package search: {e}")
            raise WingetExecutionError(f"Unexpected error: {e}")

    @staticmethod
    def install_package(
        package_id: str, silent: bool = True, retry_count: Optional[int] = None
    ) -> Dict[str, any]:
        """Install a package using winget with retry logic.

        Args:
            package_id: Package identifier to install
            silent: Whether to install silently
            retry_count: Number of retries (defaults to config value)

        Returns:
            Dictionary containing installation result information

        Raises:
            WingetNotAvailableError: If winget is not available
            AdminPrivilegesRequiredError: If admin privileges are required
            WingetExecutionError: If installation fails after retries
        """
        if retry_count is None:
            retry_count = config.retry_attempts

        logger.info(f"Starting installation of package: {package_id}")

        # Verify winget is available
        try:
            if not WingetManager.is_available():
                raise WingetNotAvailableError()
        except WingetNotAvailableError:
            # Re-raise without catching to preserve original exception type
            raise

        cmd = [
            "winget",
            "install",
            "--id",
            package_id,
            "--exact",
            "--disable-interactivity",
        ]
        if silent:
            cmd.extend(
                [
                    "--silent",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ]
            )

        last_result = None
        for attempt in range(retry_count + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt} for package: {package_id}")
                    time.sleep(2 * attempt)  # Progressive delay

                logger.debug(f"Executing command: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=config.winget_timeout,
                )

                last_result = {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "command": " ".join(cmd),
                    "attempts": attempt + 1,
                }

                if result.returncode == 0:
                    logger.info(f"Successfully installed package: {package_id}")
                    return last_result
                else:
                    # Check for specific error conditions
                    stderr_lower = result.stderr.lower()
                    stdout_lower = result.stdout.lower()

                    if any(
                        term in stderr_lower or term in stdout_lower
                        for term in ["administrator", "admin", "elevated", "privilege"]
                    ):
                        logger.error(
                            f"Admin privileges required for package: {package_id}"
                        )
                        raise AdminPrivilegesRequiredError(
                            f"Installation of {package_id} requires administrator privileges"
                        )

                    if "not found" in stderr_lower or "not found" in stdout_lower:
                        logger.error(f"Package not found: {package_id}")
                        raise PackageNotFoundError(package_id)

                    logger.warning(
                        f"Installation attempt {attempt + 1} failed for {package_id}: {result.stderr}"
                    )

                    # Don't retry for certain permanent errors
                    permanent_errors = [
                        "package already installed",
                        "newer version already installed",
                        "architecture mismatch",
                    ]
                    if any(
                        error in stderr_lower or error in stdout_lower
                        for error in permanent_errors
                    ):
                        logger.info(
                            f"Permanent error detected for {package_id}, not retrying"
                        )
                        break

            except subprocess.TimeoutExpired:
                error_msg = f"Installation timed out after {config.winget_timeout} seconds for package: {package_id}"
                logger.error(error_msg)
                if attempt < retry_count:
                    logger.info("Will retry installation after timeout...")
                    continue
                else:
                    raise WingetExecutionError(error_msg, " ".join(cmd))
            except Exception as e:
                if isinstance(
                    e, (WingetNotAvailableError, AdminPrivilegesRequiredError)
                ):
                    raise
                logger.error(f"Unexpected error installing {package_id}: {e}")
                if attempt < retry_count:
                    continue
                else:
                    raise WingetExecutionError(f"Unexpected error: {e}", " ".join(cmd))

        # All attempts failed
        error_msg = f"Failed to install {package_id} after {retry_count + 1} attempts"
        logger.error(error_msg)
        raise InstallationFailedError(
            package_id,
            last_result.get("stderr", "Unknown error") if last_result else "No result",
        )
