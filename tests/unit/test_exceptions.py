"""Unit tests for custom exception classes."""

import pytest

from humble_tools.core.exceptions import (
    APIError,
    DownloadError,
    HumbleToolsError,
    InsufficientStorageError,
    ValidationError,
)


def test_base_exception_with_user_message():
    """Test base exception supports both message and user_message."""
    error = HumbleToolsError("Technical error", user_message="User-friendly message")
    assert error.message == "Technical error"
    assert error.user_message == "User-friendly message"
    assert str(error) == "Technical error"

    # User message defaults to message if not provided
    error = HumbleToolsError("Simple message")
    assert error.user_message == "Simple message"


def test_insufficient_storage_error_includes_space_values():
    """Test InsufficientStorageError tracks required and available space."""
    error = InsufficientStorageError(required_mb=100.0, available_mb=50.0)
    assert error.required_mb == 100.0
    assert error.available_mb == 50.0
    assert "100.0MB" in error.user_message
    assert "50.0MB" in error.user_message
    assert isinstance(error, DownloadError)


def test_exception_hierarchy():
    """Test exception inheritance and catching behavior."""
    # All custom exceptions inherit from HumbleToolsError
    assert isinstance(DownloadError("test"), HumbleToolsError)
    assert isinstance(APIError("test"), HumbleToolsError)
    assert isinstance(ValidationError("test"), HumbleToolsError)
    assert isinstance(
        InsufficientStorageError(required_mb=10, available_mb=5), HumbleToolsError
    )

    # Can catch specific exception types
    with pytest.raises(DownloadError):
        raise DownloadError("test")

    # Can catch as base type
    with pytest.raises(HumbleToolsError):
        raise APIError("test")
