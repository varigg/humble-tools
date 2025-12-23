"""Custom exception hierarchy for Humble Tools application.

This module defines a minimal exception hierarchy focused on practical error
scenarios that actually occur in the application. Follows YAGNI principle -
only exceptions we'll actually use.

Exception Hierarchy
===================

HumbleToolsError (base)
├── DownloadError - Download operation failures
│   └── InsufficientStorageError - Not enough disk space
├── APIError - Humble API/CLI failures
└── ValidationError - Input validation failures

All exceptions include a user_message attribute for display in the UI.
"""


class HumbleToolsError(Exception):
    """Base exception for all Humble Tools errors.

    All custom exceptions inherit from this base class and include
    a user-friendly message suitable for display in the UI.

    Attributes:
        message: Technical error message for logging
        user_message: User-friendly message for UI display
    """

    def __init__(self, message: str, user_message: str | None = None):
        """Initialize exception with messages.

        Args:
            message: Technical error message
            user_message: User-friendly message (defaults to message if not provided)
        """
        super().__init__(message)
        self.message = message
        self.user_message = user_message or message


class DownloadError(HumbleToolsError):
    """Exception raised when download operations fail.

    This covers general download failures including network issues,
    file system errors, and other download-related problems.
    """

    def __init__(self, message: str, user_message: str | None = None):
        """Initialize download error.

        Args:
            message: Technical error message
            user_message: User-friendly message (defaults to "Download failed: {message}")
        """
        super().__init__(
            message=message,
            user_message=user_message or f"Download failed: {message}",
        )


class InsufficientStorageError(DownloadError):
    """Exception raised when there is not enough disk space for download.

    This is a specialized download error that indicates the user needs
    to free up disk space before continuing.
    """

    def __init__(self, required_mb: float, available_mb: float):
        """Initialize insufficient storage error.

        Args:
            required_mb: Required disk space in MB
            available_mb: Available disk space in MB
        """
        message = f"Insufficient disk space: need {required_mb:.1f}MB, have {available_mb:.1f}MB"
        user_message = (
            f"Not enough disk space. Need {required_mb:.1f}MB, "
            f"only {available_mb:.1f}MB available. Please free up space."
        )
        super().__init__(message=message, user_message=user_message)
        self.required_mb = required_mb
        self.available_mb = available_mb


class APIError(HumbleToolsError):
    """Exception raised when Humble API/CLI operations fail.

    This wraps errors from the humble-cli tool and Humble Bundle API,
    providing user-friendly messages for common failure scenarios.
    """

    def __init__(self, message: str, user_message: str | None = None):
        """Initialize API error.

        Args:
            message: Technical error message
            user_message: User-friendly message (defaults to "API error: {message}")
        """
        super().__init__(
            message=message,
            user_message=user_message or f"API error: {message}",
        )


class ValidationError(HumbleToolsError):
    """Exception raised when input validation fails.

    This covers validation of configuration, paths, and other inputs
    before performing operations.
    """

    def __init__(self, message: str, user_message: str | None = None):
        """Initialize validation error.

        Args:
            message: Technical error message
            user_message: User-friendly message (defaults to message)
        """
        super().__init__(
            message=message,
            user_message=user_message or message,
        )
