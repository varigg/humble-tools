"""Validation utilities for input and system checks.

This module provides validation functions for checking system resources
and validating inputs before performing operations.
"""

import os
from pathlib import Path

from .exceptions import ValidationError


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
