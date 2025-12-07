"""Tests for tracker module."""

import tempfile
from pathlib import Path

import pytest

from humble_tools.core.tracker import DownloadTracker


@pytest.fixture
def temp_tracker():
    """Create a temporary tracker for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield DownloadTracker(db_path=db_path)


class TestDownloadTracker:
    """Tests for DownloadTracker class."""
    
    def test_tracker_initialization(self):
        """Test tracker initializes with custom db path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            tracker = DownloadTracker(db_path=db_path)
            assert tracker.db_path == db_path
            assert db_path.exists()
    
    def test_mark_downloaded(self, temp_tracker):
        """Test marking a file as downloaded."""
        temp_tracker.mark_downloaded(
            file_url="test_url",
            bundle_key="bundle123",
            filename="test.epub"
        )
        
        assert temp_tracker.is_downloaded("test_url")
    
    def test_is_downloaded_returns_false_for_new_file(self, temp_tracker):
        """Test is_downloaded returns False for non-existent file."""
        assert not temp_tracker.is_downloaded("nonexistent_url")
    
    def test_get_bundle_stats_with_total(self, temp_tracker):
        """Test get_bundle_stats with total_files stored in database."""
        # Mark 2 files as downloaded with total=5
        temp_tracker.mark_downloaded("url1", "bundle123", "file1.epub", bundle_total_files=5)
        temp_tracker.mark_downloaded("url2", "bundle123", "file2.epub", bundle_total_files=5)
        
        stats = temp_tracker.get_bundle_stats("bundle123")
        
        assert stats['downloaded'] == 2
        assert stats['remaining'] == 3
        assert stats['total'] == 5
    
    def test_get_bundle_stats_without_total(self, temp_tracker):
        """Test get_bundle_stats without total_files stored."""
        # Mark 2 files as downloaded without total
        temp_tracker.mark_downloaded("url1", "bundle123", "file1.epub")
        temp_tracker.mark_downloaded("url2", "bundle123", "file2.epub")
        
        stats = temp_tracker.get_bundle_stats("bundle123")
        
        assert stats['downloaded'] == 2
        assert stats['remaining'] is None
        assert stats['total'] is None
    
    def test_get_bundle_stats_empty_bundle(self, temp_tracker):
        """Test get_bundle_stats for bundle with no downloads."""
        stats = temp_tracker.get_bundle_stats("empty_bundle")
        
        assert stats['downloaded'] == 0
        assert stats['remaining'] is None
        assert stats['total'] is None
    
    def test_get_all_stats(self, temp_tracker):
        """Test get_all_stats returns total download count."""
        # Mark files from different bundles
        temp_tracker.mark_downloaded("url1", "bundle1", "file1.epub")
        temp_tracker.mark_downloaded("url2", "bundle2", "file2.epub")
        temp_tracker.mark_downloaded("url3", "bundle1", "file3.epub")
        
        stats = temp_tracker.get_all_stats()
        
        assert stats['total_downloaded'] == 3
    
    def test_get_tracked_bundles_empty(self, temp_tracker):
        """Test get_tracked_bundles returns empty list for new tracker."""
        bundles = temp_tracker.get_tracked_bundles()
        
        assert bundles == []
    
    def test_get_tracked_bundles_with_downloads(self, temp_tracker):
        """Test get_tracked_bundles returns list of bundle keys."""
        # Mark files from different bundles
        temp_tracker.mark_downloaded("url1", "bundle_a", "file1.epub")
        temp_tracker.mark_downloaded("url2", "bundle_c", "file2.epub")
        temp_tracker.mark_downloaded("url3", "bundle_b", "file3.epub")
        temp_tracker.mark_downloaded("url4", "bundle_a", "file4.epub")
        
        bundles = temp_tracker.get_tracked_bundles()
        
        # Should return unique bundle keys in sorted order
        assert bundles == ["bundle_a", "bundle_b", "bundle_c"]
    
    def test_get_tracked_bundles_deduplicates(self, temp_tracker):
        """Test get_tracked_bundles returns unique bundle keys."""
        # Mark multiple files from same bundle
        temp_tracker.mark_downloaded("url1", "bundle123", "file1.epub")
        temp_tracker.mark_downloaded("url2", "bundle123", "file2.epub")
        temp_tracker.mark_downloaded("url3", "bundle123", "file3.epub")
        
        bundles = temp_tracker.get_tracked_bundles()
        
        # Should only return "bundle123" once
        assert bundles == ["bundle123"]
    
    def test_get_downloaded_files(self, temp_tracker):
        """Test get_downloaded_files returns all downloads."""
        temp_tracker.mark_downloaded("url1", "bundle1", "file1.epub")
        temp_tracker.mark_downloaded("url2", "bundle2", "file2.epub")
        
        files = temp_tracker.get_downloaded_files()
        
        assert len(files) == 2
        # Check that files contain expected data (filename, bundle_key, timestamp)
        filenames = [f[0] for f in files]
        assert "file1.epub" in filenames
        assert "file2.epub" in filenames
    
    def test_get_downloaded_files_filtered_by_bundle(self, temp_tracker):
        """Test get_downloaded_files filtered by bundle_key."""
        temp_tracker.mark_downloaded("url1", "bundle1", "file1.epub")
        temp_tracker.mark_downloaded("url2", "bundle2", "file2.epub")
        temp_tracker.mark_downloaded("url3", "bundle1", "file3.epub")
        
        files = temp_tracker.get_downloaded_files(bundle_key="bundle1")
        
        assert len(files) == 2
        filenames = [f[0] for f in files]
        assert "file1.epub" in filenames
        assert "file3.epub" in filenames
        assert "file2.epub" not in filenames
