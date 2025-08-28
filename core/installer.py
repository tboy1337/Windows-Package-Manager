"""Installer module for handling package installations with retry logic."""

import threading
import time
from typing import Any, Callable, Dict, List, Optional

from .config import config
from .exceptions import (
    AdminPrivilegesRequiredError,
    InstallationFailedError,
    PackageNotFoundError,
    WingetExecutionError,
    WingetNotAvailableError,
)
from .logger import logger
from .winget_manager import WingetManager


class InstallationProgress:
    """Track installation progress and results."""

    def __init__(self, total_packages: int) -> None:
        """Initialize progress tracking.

        Args:
            total_packages: Total number of packages to install
        """
        self.total_packages = total_packages
        self.completed_packages = 0
        self.successful_installations = 0
        self.failed_installations = 0
        self.skipped_installations = 0
        self.current_package = ""
        self.results: Dict[str, Dict[str, Any]] = {}
        self.start_time = time.time()
        self.lock = threading.Lock()

    def update(self, package_id: str, result: Dict[str, Any]) -> None:
        """Update progress with package installation result.

        Args:
            package_id: Package ID that was processed
            result: Installation result dictionary
        """
        with self.lock:
            self.results[package_id] = result
            self.completed_packages += 1

            if result.get("success", False):
                self.successful_installations += 1
            elif result.get("skipped", False):
                self.skipped_installations += 1
            else:
                self.failed_installations += 1

    @property
    def progress_percentage(self) -> float:
        """Get installation progress as percentage."""
        if self.total_packages == 0:
            return 100.0
        return (self.completed_packages / self.total_packages) * 100

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    def get_summary(self) -> Dict[str, Any]:
        """Get installation summary."""
        return {
            "total": self.total_packages,
            "completed": self.completed_packages,
            "successful": self.successful_installations,
            "failed": self.failed_installations,
            "skipped": self.skipped_installations,
            "progress_percentage": self.progress_percentage,
            "elapsed_time": self.elapsed_time,
            "results": self.results.copy(),
        }


class Installer:
    """Handles package installation with retry logic and threading support."""

    def __init__(self) -> None:
        """Initialize the installer with a WingetManager instance."""
        self.winget = WingetManager()
        self._current_progress: Optional[InstallationProgress] = None
        self._installation_thread: Optional[threading.Thread] = None

    @property
    def is_installing(self) -> bool:
        """Check if installation is currently in progress."""
        return (
            self._installation_thread is not None
            and self._installation_thread.is_alive()
        )

    def get_progress(self) -> Optional[InstallationProgress]:
        """Get current installation progress."""
        return self._current_progress

    def install_packages(
        self,
        package_ids: List[str],
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        progress_callback: Optional[Callable[[InstallationProgress], None]] = None,
        silent: bool = True,
        stop_on_first_failure: bool = False,
    ) -> threading.Thread:
        """Install multiple packages in a background thread.

        Args:
            package_ids: List of package IDs to install
            callback: Optional callback function called for each package result
            progress_callback: Optional callback for progress updates
            silent: Whether to install packages silently
            stop_on_first_failure: Whether to stop installation on first failure

        Returns:
            Thread object handling the installation

        Raises:
            RuntimeError: If installation is already in progress
        """
        if self.is_installing:
            raise RuntimeError("Installation already in progress")

        if not package_ids:
            logger.warning("No packages to install")
            return threading.Thread()

        logger.info(f"Starting installation of {len(package_ids)} packages")
        self._current_progress = InstallationProgress(len(package_ids))

        def install_thread() -> None:
            """Main installation thread function."""
            try:
                for i, pkg_id in enumerate(package_ids, 1):
                    if self._current_progress:
                        self._current_progress.current_package = pkg_id

                    logger.info(f"Installing package {i}/{len(package_ids)}: {pkg_id}")

                    try:
                        # Use the enhanced install_package method
                        result = self.winget.install_package(pkg_id, silent=silent)
                        logger.info(f"Successfully installed {pkg_id}")

                    except AdminPrivilegesRequiredError as e:
                        logger.error(f"Admin privileges required for {pkg_id}: {e}")
                        result = {
                            "success": False,
                            "error_type": "admin_required",
                            "error_message": str(e),
                            "package_id": pkg_id,
                            "skipped": True,
                        }

                    except PackageNotFoundError as e:
                        logger.error(f"Package not found {pkg_id}: {e}")
                        result = {
                            "success": False,
                            "error_type": "not_found",
                            "error_message": str(e),
                            "package_id": pkg_id,
                            "skipped": True,
                        }

                    except (
                        WingetNotAvailableError,
                        WingetExecutionError,
                        InstallationFailedError,
                    ) as e:
                        logger.error(f"Installation failed for {pkg_id}: {e}")
                        result = {
                            "success": False,
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "package_id": pkg_id,
                        }

                        if stop_on_first_failure:
                            logger.warning("Stopping installation due to failure")
                            if self._current_progress:
                                self._current_progress.update(pkg_id, result)
                            if callback:
                                callback(pkg_id, result)
                            break

                    except Exception as e:
                        logger.exception(f"Unexpected error installing {pkg_id}: {e}")
                        result = {
                            "success": False,
                            "error_type": "unexpected_error",
                            "error_message": str(e),
                            "package_id": pkg_id,
                        }

                        if stop_on_first_failure:
                            if self._current_progress:
                                self._current_progress.update(pkg_id, result)
                            if callback:
                                callback(pkg_id, result)
                            break

                    # Update progress
                    if self._current_progress:
                        self._current_progress.update(pkg_id, result)
                        if progress_callback:
                            progress_callback(self._current_progress)

                    # Call result callback
                    if callback:
                        callback(pkg_id, result)

                    # Small delay between installations to avoid overwhelming the system
                    if i < len(package_ids):  # Don't sleep after the last package
                        time.sleep(0.5)

                # Log final summary
                if self._current_progress:
                    summary = self._current_progress.get_summary()
                    logger.info(
                        f"Installation complete. "
                        f"Successful: {summary['successful']}, "
                        f"Failed: {summary['failed']}, "
                        f"Skipped: {summary['skipped']}, "
                        f"Time: {summary['elapsed_time']:.1f}s"
                    )

            except Exception as e:
                logger.exception(f"Critical error in installation thread: {e}")
            finally:
                logger.debug("Installation thread completed")

        self._installation_thread = threading.Thread(
            target=install_thread, name=f"PackageInstaller-{len(package_ids)}pkgs"
        )
        self._installation_thread.start()
        return self._installation_thread

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for current installation to complete.

        Args:
            timeout: Maximum time to wait in seconds (None for no timeout)

        Returns:
            True if installation completed, False if timeout occurred
        """
        if not self._installation_thread:
            return True

        self._installation_thread.join(timeout=timeout)
        return not self._installation_thread.is_alive()

    def get_installation_summary(self) -> Optional[Dict[str, Any]]:
        """Get summary of the last installation."""
        if self._current_progress:
            return self._current_progress.get_summary()
        return None
