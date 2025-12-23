"""Tests for format_utils.py."""

from humble_tools.core.format_utils import FormatUtils


def test_format_file_size():
    """Test format_file_size."""
    assert FormatUtils.format_file_size(100) == "100.0 B"
    assert FormatUtils.format_file_size(1024) == "1.0 KB"
    assert FormatUtils.format_file_size(1024 * 1024) == "1.0 MB"
    assert FormatUtils.format_file_size(1024 * 1024 * 1024) == "1.0 GB"
    assert FormatUtils.format_file_size(1536) == "1.5 KB"


def test_format_download_progress():
    """Test format_download_progress."""
    assert FormatUtils.format_download_progress(5, 10) == "50.0%"
    assert FormatUtils.format_download_progress(0, 10) == "0.0%"
    assert FormatUtils.format_download_progress(10, 10) == "100.0%"
    assert FormatUtils.format_download_progress(5, 0) == "0%"
    assert FormatUtils.format_download_progress(5, None) == "5/?"


def test_format_bundle_stats():
    """Test format_bundle_stats."""
    assert FormatUtils.format_bundle_stats(5, 10) == "5/10"
    assert FormatUtils.format_bundle_stats(5, None) == "5/?"


def test_truncate_string():
    """Test truncate_string."""
    assert FormatUtils.truncate_string("hello", 10) == "hello"
    assert FormatUtils.truncate_string("hello world", 5) == "he..."
    assert FormatUtils.truncate_string("hello world", 8) == "hello..."
    assert FormatUtils.truncate_string("abc", 3) == "abc"
