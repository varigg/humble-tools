"""Unit tests for validation utilities."""

from pathlib import Path
from unittest.mock import patch

import pytest
from humble_tools.core.exceptions import ValidationError
from humble_tools.core.validation import validate_output_directory


def test_validate_output_directory_valid(tmp_path):
    """Test no error for valid writable directory."""
    validate_output_directory(tmp_path)


def test_validate_output_directory_invalid(tmp_path):
    """Test errors for invalid directory scenarios."""
    # Nonexistent directory
    with pytest.raises(ValidationError):
        validate_output_directory(Path("/tmp/nonexistent_12345"))

    # File instead of directory
    test_file = tmp_path / "file.txt"
    test_file.write_text("test")
    with pytest.raises(ValidationError):
        validate_output_directory(test_file)

    # Not writable
    with patch("os.access", return_value=False):
        with pytest.raises(ValidationError):
            validate_output_directory(tmp_path)
