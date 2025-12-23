"""Validation utilities for input and system checks.

This module provides validation functions for checking system resources
and validating inputs before performing operations.
"""

import os
import shutil
from pathlib import Path

from .exceptions import InsufficientStorageError, ValidationError


def check_disk_space(path: Path, required_bytes: int) -> None:
    """Check if sufficient disk space is available at the given path.

    Args:
        path: Directory path to check disk space for
        required_bytes: Number of bytes required

    Raises:
        InsufficientStorageError: If available space is less than required
        ValidationError: If path does not exist or is not accessible
    """
    # Ensure path exists
    if not path.exists():
        raise ValidationError(
            f"Path does not exist: {path}",
            user_message=f"Output directory does not exist: {path}",
        )

    # Check if path is accessible
    if not path.is_dir():
        raise ValidationError(
            f"Path is not a directory: {path}",
            user_message=f"Output path is not a directory: {path}",
        )

    # Get available disk space
    try:
        disk_usage = shutil.disk_usage(path)
        available_bytes = disk_usage.free
    except OSError as e:
        raise ValidationError(
            f"Failed to check disk space: {e}",
            user_message=f"Cannot access output directory: {path}",
        ) from e

    # Check if sufficient space available
    if available_bytes < required_bytes:
        required_mb = required_bytes / (1024 * 1024)
        available_mb = available_bytes / (1024 * 1024)
        raise InsufficientStorageError(
            required_mb=required_mb, available_mb=available_mb
        )


def validate_output_directory(path: Path) -> None:
    """Validate that output directory exists and is writable.

    Args:
        path: Directory path to validate

    Raises:
        ValidationError: If directory is invalid or not writable
    """
    # Check if directory exists
    if not path.exists():
        raise ValidationError(
            f"Output directory does not exist: {path}",
            user_message=f"Output directory not found: {path}",
        )

    # Check if it's actually a directory
    if not path.is_dir():
        raise ValidationError(
            f"Output path is not a directory: {path}",
            user_message=f"Output path must be a directory: {path}",
        )

    # Check if directory is writable
    if not os.access(path, os.W_OK):
        raise ValidationError(
            f"Output directory is not writable: {path}",
            user_message=f"Cannot write to output directory: {path}. Check permissions.",
        )
