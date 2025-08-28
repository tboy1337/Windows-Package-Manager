"""Custom exceptions for Windows Package Manager."""
from typing import Optional


class WingetPackageManagerError(Exception):
    """Base exception for Windows Package Manager."""

    def __init__(self, message: str, error_code: Optional[int] = None) -> None:
        """Initialize exception.

        Args:
            message: Error message
            error_code: Optional error code
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class WingetNotAvailableError(WingetPackageManagerError):
    """Raised when winget is not available on the system."""

    def __init__(self, message: str = "Winget is not available on this system") -> None:
        super().__init__(message, 1001)


class WingetExecutionError(WingetPackageManagerError):
    """Raised when winget command execution fails."""

    def __init__(
        self, message: str, command: Optional[str] = None, return_code: Optional[int] = None
    ) -> None:
        super().__init__(message, 1002)
        self.command = command
        self.return_code = return_code


class AdminPrivilegesRequiredError(WingetPackageManagerError):
    """Raised when administrator privileges are required."""

    def __init__(self, message: str = "Administrator privileges are required") -> None:
        super().__init__(message, 1003)


class PackageNotFoundError(WingetPackageManagerError):
    """Raised when a package is not found."""

    def __init__(self, package_id: str) -> None:
        message = f"Package '{package_id}' not found"
        super().__init__(message, 1004)
        self.package_id = package_id


class InstallationFailedError(WingetPackageManagerError):
    """Raised when package installation fails."""

    def __init__(self, package_id: str, reason: str) -> None:
        message = f"Installation of '{package_id}' failed: {reason}"
        super().__init__(message, 1005)
        self.package_id = package_id
        self.reason = reason


class DatabaseError(WingetPackageManagerError):
    """Raised when database operations fail."""

    def __init__(self, message: str, operation: Optional[str] = None) -> None:
        super().__init__(message, 1006)
        self.operation = operation


class ConfigurationError(WingetPackageManagerError):
    """Raised when configuration issues occur."""

    def __init__(self, message: str, config_key: Optional[str] = None) -> None:
        super().__init__(message, 1007)
        self.config_key = config_key


class UIError(WingetPackageManagerError):
    """Raised when UI operations fail."""

    def __init__(self, message: str, component: Optional[str] = None) -> None:
        super().__init__(message, 1008)
        self.component = component


class FileOperationError(WingetPackageManagerError):
    """Raised when file operations fail."""

    def __init__(self, message: str, file_path: Optional[str] = None) -> None:
        super().__init__(message, 1009)
        self.file_path = file_path
