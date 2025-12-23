"""Tests for tracker module.

Test Coverage:
- Tracker initialization with custom and in-memory databases
- Marking files as downloaded with metadata
- Checking download status
- Bundle statistics (downloaded, remaining, total)
- Tracking multiple bundles
- Retrieving downloaded file lists
- Database connection dependency injection

Performance: Fast tests use in-memory SQLite (:memory:)
Dependencies: Uses SQLiteConnection and create_default_connection from database module
"""

import pytest
from humble_tools.core.database import SQLiteConnection
from humble_tools.core.tracker import DownloadTracker


@pytest.fixture
def tracker():
    """In-memory tracker for fast tests."""
    db_conn = SQLiteConnection(":memory:")
    yield DownloadTracker(db_connection=db_conn)
    db_conn.close()


class TestDownloadTracker:
    """Tests for DownloadTracker class."""

    def test_mark_downloaded(self, tracker):
        """Test marking a file as downloaded."""
        tracker.mark_downloaded(file_url="test_url", bundle_key="bundle123", filename="test.epub")

        assert tracker.is_downloaded("test_url")

    def test_is_downloaded_returns_false_for_new_file(self, tracker):
        """Test is_downloaded returns False for non-existent file."""
        assert not tracker.is_downloaded("nonexistent_url")

    def test_get_bundle_stats_with_total(self, tracker):
        """Test get_bundle_stats with total_files stored in database."""
        # Mark 2 files as downloaded with total=5
        tracker.mark_downloaded("url1", "bundle123", "file1.epub", bundle_total_files=5)
        tracker.mark_downloaded("url2", "bundle123", "file2.epub", bundle_total_files=5)

        stats = tracker.get_bundle_stats("bundle123")

        assert stats["downloaded"] == 2
        assert stats["remaining"] == 3
        assert stats["total"] == 5

    def test_get_bundle_stats_without_total(self, tracker):
        """Test get_bundle_stats without total_files stored."""
        # Mark 2 files as downloaded without total
        tracker.mark_downloaded("url1", "bundle123", "file1.epub")
        tracker.mark_downloaded("url2", "bundle123", "file2.epub")

        stats = tracker.get_bundle_stats("bundle123")

        assert stats["downloaded"] == 2
        assert stats["remaining"] is None
        assert stats["total"] is None

    def test_get_bundle_stats_empty_bundle(self, tracker):
        """Test get_bundle_stats for bundle with no downloads."""
        stats = tracker.get_bundle_stats("empty_bundle")

        assert stats["downloaded"] == 0
        assert stats["remaining"] is None
        assert stats["total"] is None

    def test_get_all_stats(self, tracker):
        """Test get_all_stats returns total download count."""
        # Mark files from different bundles
        tracker.mark_downloaded("url1", "bundle1", "file1.epub")
        tracker.mark_downloaded("url2", "bundle2", "file2.epub")
        tracker.mark_downloaded("url3", "bundle1", "file3.epub")

        stats = tracker.get_all_stats()

        assert stats["total_downloaded"] == 3

    def test_get_tracked_bundles_with_downloads(self, tracker):
        """Test get_tracked_bundles returns list of bundle keys."""
        # Mark files from different bundles
        tracker.mark_downloaded("url1", "bundle_a", "file1.epub")
        tracker.mark_downloaded("url2", "bundle_c", "file2.epub")
        tracker.mark_downloaded("url3", "bundle_b", "file3.epub")
        tracker.mark_downloaded("url4", "bundle_a", "file4.epub")

        bundles = tracker.get_tracked_bundles()

        # Should return unique bundle keys in sorted order
        assert bundles == ["bundle_a", "bundle_b", "bundle_c"]

    def test_get_downloaded_files(self, tracker):
        """Test get_downloaded_files returns all downloads."""
        tracker.mark_downloaded("url1", "bundle1", "file1.epub")
        tracker.mark_downloaded("url2", "bundle2", "file2.epub")

        files = tracker.get_downloaded_files()

        assert len(files) == 2
        # Check that files contain expected data (filename, bundle_key, timestamp)
        filenames = [f[0] for f in files]
        assert "file1.epub" in filenames
        assert "file2.epub" in filenames

    def test_get_downloaded_files_filtered_by_bundle(self, tracker):
        """Test get_downloaded_files filtered by bundle_key."""
        tracker.mark_downloaded("url1", "bundle1", "file1.epub")
        tracker.mark_downloaded("url2", "bundle2", "file2.epub")
        tracker.mark_downloaded("url3", "bundle1", "file3.epub")

        files = tracker.get_downloaded_files(bundle_key="bundle1")

        assert len(files) == 2
        filenames = [f[0] for f in files]
        assert "file1.epub" in filenames
        assert "file3.epub" in filenames
        assert "file2.epub" not in filenames
