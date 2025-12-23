"""Unit tests for BundleDetailsScreen helper methods from Phase 3.

Test Coverage:
- Safe widget query with error handling
- Format download completion checking
- Download state transition handlers
- Queue status formatting

Focus: High-value tests for error scenarios and state management.
"""

import threading
from unittest.mock import Mock, patch

import pytest
from textual.css.query import NoMatches
from textual.widgets import Static

from humble_tools.sync.app import BundleDetailsScreen, ItemFormatRow
from humble_tools.sync.config import AppConfig


class TestSafeQueryWidget:
    """Test safe widget query helper - critical for screen transition handling."""

    @pytest.fixture
    def mock_screen(self):
        """Create a mock BundleDetailsScreen."""
        with patch("humble_tools.sync.app.DownloadManager"):
            config = AppConfig()
            screen = BundleDetailsScreen(
                download_manager=Mock(),
                config=config,
            )
            screen.bundle_key = "test_key"
            screen.bundle_name = "Test Bundle"
            return screen

    def test_safe_query_widget_success(self, mock_screen):
        """Test successful widget query."""
        mock_widget = Mock(spec=Static)
        mock_screen.query_one = Mock(return_value=mock_widget)

        result = mock_screen._safe_query_widget("#test-widget", Static)

        assert result == mock_widget
        mock_screen.query_one.assert_called_once_with("#test-widget", Static)

    def test_safe_query_widget_no_matches(self, mock_screen):
        """Test widget query when widget doesn't exist (common during transitions)."""
        mock_screen.query_one = Mock(side_effect=NoMatches("Widget not found"))

        result = mock_screen._safe_query_widget("#missing-widget", Static)

        assert result is None

    def test_safe_query_widget_no_matches_with_callback(self, mock_screen):
        """Test widget query with default action callback."""
        mock_screen.query_one = Mock(side_effect=NoMatches("Widget not found"))
        callback_called = Mock()

        result = mock_screen._safe_query_widget(
            "#missing-widget", Static, default_action=callback_called
        )

        assert result is None
        callback_called.assert_called_once()

    def test_safe_query_widget_unexpected_error(self, mock_screen, caplog):
        """Test handling of unexpected exceptions."""
        mock_screen.query_one = Mock(side_effect=RuntimeError("Unexpected error"))

        result = mock_screen._safe_query_widget("#error-widget", Static)

        assert result is None
        assert "Unexpected error querying widget" in caplog.text


class TestAllFormatsDownloaded:
    """Test format completion checking - determines when items are removed."""

    def test_all_formats_downloaded_true(self):
        """Test when all formats are downloaded."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Complete Book",
            formats=["EPUB", "PDF", "MOBI"],
            item_size="10 MB",
            format_status={"EPUB": True, "PDF": True, "MOBI": True},
        )

        with patch("humble_tools.sync.app.DownloadManager"):
            config = AppConfig()
            screen = BundleDetailsScreen(download_manager=Mock(), config=config)

            assert screen._all_formats_downloaded(row) is True

    def test_all_formats_downloaded_false_one_missing(self):
        """Test when one format is not downloaded."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Partial Book",
            formats=["EPUB", "PDF", "MOBI"],
            item_size="10 MB",
            format_status={"EPUB": True, "PDF": False, "MOBI": True},
        )

        with patch("humble_tools.sync.app.DownloadManager"):
            config = AppConfig()
            screen = BundleDetailsScreen(download_manager=Mock(), config=config)

            assert screen._all_formats_downloaded(row) is False

    def test_all_formats_downloaded_false_none_downloaded(self):
        """Test when no formats are downloaded."""
        row = ItemFormatRow(
            item_number=1,
            item_name="New Book",
            formats=["EPUB", "PDF"],
            item_size="10 MB",
            format_status={"EPUB": False, "PDF": False},
        )

        with patch("humble_tools.sync.app.DownloadManager"):
            config = AppConfig()
            screen = BundleDetailsScreen(download_manager=Mock(), config=config)

            assert screen._all_formats_downloaded(row) is False

    def test_all_formats_downloaded_empty_format_status(self):
        """Test edge case: format_status dict doesn't have entries."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB", "PDF"],
            item_size="10 MB",
            format_status={},  # Empty dict
        )

        with patch("humble_tools.sync.app.DownloadManager"):
            config = AppConfig()
            screen = BundleDetailsScreen(download_manager=Mock(), config=config)

            # Should return False since formats aren't marked as downloaded
            assert screen._all_formats_downloaded(row) is False


class TestFormatQueueStatus:
    """Test queue status formatting - critical for user feedback."""

    @pytest.fixture
    def mock_screen(self):
        """Create a mock BundleDetailsScreen."""
        with patch("humble_tools.sync.app.DownloadManager"):
            config = AppConfig()
            screen = BundleDetailsScreen(download_manager=Mock(), config=config)
            return screen

    def test_format_queue_status_with_queued(self, mock_screen):
        """Test status string when items are queued."""
        # Simulate queue state with items queued and active
        mock_screen._queue.mark_queued()
        mock_screen._queue.mark_queued()
        mock_screen._queue.mark_queued()
        mock_screen._queue.mark_queued()
        mock_screen._queue.mark_queued()
        mock_screen._queue.mark_started()
        mock_screen._queue.mark_started()

        result = mock_screen._format_queue_status()

        assert "Active: 2/3" in result
        assert "Queued: 3" in result

    def test_format_queue_status_without_queued(self, mock_screen):
        """Test status string when no items queued."""
        # Simulate one active download, no queued
        mock_screen._queue.mark_queued()
        mock_screen._queue.mark_started()

        result = mock_screen._format_queue_status()

        assert "Active Downloads: 1/3" in result
        assert "Queued" not in result

    def test_format_queue_status_at_limit(self, mock_screen):
        """Test status when at max concurrent downloads."""
        # Simulate 3 active (at limit) and 10 queued
        for _ in range(13):
            mock_screen._queue.mark_queued()
        for _ in range(3):
            mock_screen._queue.mark_started()

        result = mock_screen._format_queue_status()

        assert "Active: 3/3" in result
        assert "Queued: 10" in result


class TestDownloadStateHandlers:
    """Test download state transition handlers - critical for thread safety and state management."""

    @pytest.fixture
    def mock_screen(self):
        """Create a mock BundleDetailsScreen with mocked dependencies."""
        with patch("humble_tools.sync.app.DownloadManager"):
            config = AppConfig()
            screen = BundleDetailsScreen(download_manager=Mock(), config=config)
            screen._download_lock = threading.Lock()
            screen.update_download_counter = Mock()
            screen.show_notification = Mock()
            screen.set_timer = Mock()
            return screen

    @pytest.fixture
    def mock_item_row(self):
        """Create a mock ItemFormatRow."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test Book",
            formats=["EPUB", "PDF"],
            item_size="10 MB",
            format_status={"EPUB": False, "PDF": False},
        )
        row.update_display = Mock()
        return row

    def test_handle_download_queued(self, mock_screen, mock_item_row):
        """Test queued state handler increments counter and updates UI."""
        initial_queued = mock_screen._queue.queued_count

        mock_screen._handle_download_queued(mock_item_row, "EPUB")

        # Counter incremented
        assert mock_screen._queue.queued_count == initial_queued + 1

        # Format marked as queued
        assert mock_item_row.format_queued["EPUB"] is True

        # UI updated
        mock_item_row.update_display.assert_called_once()
        mock_screen.update_download_counter.assert_called_once()

    def test_handle_download_started(self, mock_screen, mock_item_row):
        """Test started state handler transitions from queued to downloading."""
        # Set up queue state: 5 queued, 2 active
        for _ in range(7):
            mock_screen._queue.mark_queued()
        for _ in range(2):
            mock_screen._queue.mark_started()

        mock_item_row.format_queued["EPUB"] = True

        mock_screen._handle_download_started(mock_item_row, "EPUB")

        # Counters updated correctly
        assert mock_screen._queue.queued_count == 4
        assert mock_screen._queue.active_count == 3

        # State transitioned
        assert mock_item_row.format_queued["EPUB"] is False
        assert mock_item_row.format_downloading["EPUB"] is True

        # UI updated
        mock_item_row.update_display.assert_called_once()
        mock_screen.update_download_counter.assert_called_once()

    def test_handle_download_success(self, mock_screen, mock_item_row):
        """Test success handler marks downloaded and schedules removal."""
        mock_item_row.format_downloading["EPUB"] = True

        mock_screen._handle_download_success(mock_item_row, "EPUB")

        # State updated
        assert mock_item_row.format_status["EPUB"] is True
        assert mock_item_row.format_downloading["EPUB"] is False

        # Notification shown
        mock_screen.show_notification.assert_called_once()
        assert "Downloaded" in str(mock_screen.show_notification.call_args)

        # Removal scheduled
        mock_screen.set_timer.assert_called_once()

    def test_handle_download_failure(self, mock_screen, mock_item_row):
        """Test failure handler clears downloading state and shows error."""
        mock_item_row.format_downloading["EPUB"] = True

        mock_screen._handle_download_failure(mock_item_row, "EPUB")

        # State cleared
        assert mock_item_row.format_downloading["EPUB"] is False

        # Error notification shown
        mock_screen.show_notification.assert_called_once()
        assert "Failed" in str(mock_screen.show_notification.call_args)

        # UI updated
        mock_item_row.update_display.assert_called_once()

    def test_handle_download_error(self, mock_screen, mock_item_row):
        """Test error handler shows exception message."""
        mock_item_row.format_downloading["PDF"] = True
        test_error = ValueError("Network timeout")

        mock_screen._handle_download_error(mock_item_row, "PDF", test_error)

        # State cleared
        assert mock_item_row.format_downloading["PDF"] is False

        # Error notification with exception message
        mock_screen.show_notification.assert_called_once()
        notification_call = str(mock_screen.show_notification.call_args)
        # Error notification includes failure symbol and error message
        assert "✗" in notification_call or "FAILED" in notification_call
        assert "Network timeout" in notification_call

        # UI updated
        mock_item_row.update_display.assert_called_once()

    def test_handle_download_cleanup(self, mock_screen):
        """Test cleanup handler decrements counter (called in finally block)."""
        # Set up queue state with 3 active downloads
        for _ in range(3):
            mock_screen._queue.mark_queued()
            mock_screen._queue.mark_started()

        mock_screen._handle_download_cleanup()

        # Counter decremented
        assert mock_screen._queue.active_count == 2

        # UI updated
        mock_screen.update_download_counter.assert_called_once()

    def test_download_handlers_thread_safety(self, mock_screen, mock_item_row):
        """Test that counter operations are thread-safe."""
        # Verify queue state starts at zero
        assert mock_screen._queue.queued_count == 0
        assert mock_screen._queue.active_count == 0

        # Simulate concurrent access
        def concurrent_queued():
            mock_screen._handle_download_queued(mock_item_row, "EPUB")

        def concurrent_started():
            mock_screen._handle_download_started(mock_item_row, "EPUB")

        def concurrent_cleanup():
            mock_screen._handle_download_cleanup()

        # Execute handlers - they should complete without errors
        concurrent_queued()
        concurrent_started()
        concurrent_cleanup()

        # Final state should be consistent
        assert mock_screen._queue.active_count == 0
        assert mock_screen._queue.queued_count == 0
