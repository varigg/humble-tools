"""Unit tests for validation utilities."""

from pathlib import Path
from unittest.mock import patch

import pytest

from humble_tools.core.exceptions import InsufficientStorageError, ValidationError
from humble_tools.core.validation import check_disk_space, validate_output_directory


def test_check_disk_space_sufficient(tmp_path):
    """Test no error when sufficient disk space available."""
    check_disk_space(tmp_path, required_bytes=1024)  # 1KB - should always pass


def test_check_disk_space_insufficient(tmp_path):
    """Test error when insufficient disk space."""
    with patch("shutil.disk_usage") as mock_usage:
        mock_usage.return_value = type("Usage", (), {"free": 50 * 1024 * 1024})()

        with pytest.raises(InsufficientStorageError) as exc_info:
            check_disk_space(tmp_path, required_bytes=100 * 1024 * 1024)

        error = exc_info.value
        assert error.required_mb == pytest.approx(100.0, rel=0.1)
        assert error.available_mb == pytest.approx(50.0, rel=0.1)


def test_check_disk_space_invalid_path():
    """Test error for nonexistent or invalid paths."""
    with pytest.raises(ValidationError):
        check_disk_space(Path("/tmp/nonexistent_12345"), required_bytes=1024)


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
