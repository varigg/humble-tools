"""Tests for download_manager module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from humble_tools.core.download_manager import DownloadManager, _create_file_id


@pytest.fixture
def mock_tracker():
    """Create a mock tracker for testing."""
    return Mock()


@pytest.fixture
def epub_manager(mock_tracker):
    """Create a DownloadManager with a mock tracker."""
    return DownloadManager(tracker=mock_tracker)


class TestCreateFileId:
    """Tests for the _create_file_id helper function."""

    @pytest.mark.parametrize(
        "bundle_key,item_number,format_name,expected",
        [
            ("bundle123", 1, "epub", "bundle123_1_epub"),
            ("bundle456", 2, "EPUB", "bundle456_2_epub"),  # uppercase format
            ("bundle789", 3, "PdF", "bundle789_3_pdf"),  # mixed case
            (
                "bundle-2024-special",
                10,
                "mobi",
                "bundle-2024-special_10_mobi",
            ),  # special chars
            ("bundle", 999, "azw3", "bundle_999_azw3"),  # large number
        ],
    )
    def test_create_file_id(self, bundle_key, item_number, format_name, expected):
        """Test file ID creation with various inputs."""
        file_id = _create_file_id(bundle_key, item_number, format_name)
        assert file_id == expected


class TestDownloadManagerInit:
    """Tests for DownloadManager initialization."""

    @pytest.mark.parametrize(
        "tracker_arg,should_create",
        [
            (Mock(), False),  # with provided tracker
            (None, True),  # with None explicitly
        ],
    )
    def test_init(self, tracker_arg, should_create):
        """Test initialization with and without tracker."""
        manager = DownloadManager(tracker=tracker_arg)
        if should_create:
            assert manager.tracker is not None
        else:
            assert manager.tracker == tracker_arg

    def test_init_without_args(self):
        """Test initialization without any args creates default tracker."""
        manager = DownloadManager()
        assert manager.tracker is not None


class TestDownloadManagerGetBundleItems:
    """Tests for get_bundle_items method."""

    @patch("humble_tools.core.download_manager.get_bundle_details")
    @patch("humble_tools.core.download_manager.parse_bundle_details")
    def test_get_bundle_items_adds_download_status(self, mock_parse, mock_get_details):
        """Test that download status is added to each item format."""
        # Setup mocks
        mock_get_details.return_value = "raw details"
        mock_parse.return_value = {
            "name": "Test Bundle",
            "purchased": "2024-01-01",
            "amount": "$10",
            "total_size": "100 MiB",
            "items": [
                {
                    "number": 1,
                    "name": "Book 1",
                    "formats": ["EPUB", "PDF"],
                    "size": "50 MiB",
                },
                {
                    "number": 2,
                    "name": "Book 2",
                    "formats": ["EPUB", "MOBI", "PDF"],
                    "size": "50 MiB",
                },
            ],
            "keys": [],
        }

        mock_tracker = Mock()
        mock_tracker.is_downloaded.side_effect = [
            True,  # bundle_1_epub
            False,  # bundle_1_pdf
            False,  # bundle_2_epub
            True,  # bundle_2_mobi
            False,  # bundle_2_pdf
        ]

        manager = DownloadManager(tracker=mock_tracker)
        result = manager.get_bundle_items("bundle")

        # Check that format_status was added
        assert "format_status" in result["items"][0]
        assert "format_status" in result["items"][1]

        # Check download status
        assert result["items"][0]["format_status"]["EPUB"] is True
        assert result["items"][0]["format_status"]["PDF"] is False

        assert result["items"][1]["format_status"]["EPUB"] is False
        assert result["items"][1]["format_status"]["MOBI"] is True
        assert result["items"][1]["format_status"]["PDF"] is False

    @patch("humble_tools.core.download_manager.get_bundle_details")
    @patch("humble_tools.core.download_manager.parse_bundle_details")
    def test_get_bundle_items_with_no_items(self, mock_parse, mock_get_details):
        """Test handling bundle with no items."""
        mock_get_details.return_value = "raw details"
        mock_parse.return_value = {
            "name": "Empty Bundle",
            "purchased": "2024-01-01",
            "amount": "$0",
            "total_size": "0 B",
            "items": [],
            "keys": [],
        }

        manager = DownloadManager(tracker=Mock())
        result = manager.get_bundle_items("bundle")

        assert result["items"] == []
        assert result["keys"] == []

    @patch("humble_tools.core.download_manager.get_bundle_details")
    @patch("humble_tools.core.download_manager.parse_bundle_details")
    def test_get_bundle_items_calls_create_file_id_correctly(
        self, mock_parse, mock_get_details
    ):
        """Test that _create_file_id is called with correct parameters."""
        mock_get_details.return_value = "raw details"
        mock_parse.return_value = {
            "name": "Test Bundle",
            "items": [
                {"number": 5, "name": "Book", "formats": ["EPUB"], "size": "10 MiB"}
            ],
            "keys": [],
            "purchased": "",
            "amount": "",
            "total_size": "",
        }

        mock_tracker = Mock()
        mock_tracker.is_downloaded.return_value = False

        manager = DownloadManager(tracker=mock_tracker)
        manager.get_bundle_items("test_bundle_key")

        # Verify is_downloaded was called with correct file_id
        mock_tracker.is_downloaded.assert_called_once_with("test_bundle_key_5_epub")


class TestDownloadManagerDownloadItem:
    """Tests for download_item method."""

    @pytest.mark.parametrize(
        "download_success,should_mark",
        [
            (True, True),  # successful download
            (False, False),  # failed download
        ],
    )
    @patch("humble_tools.core.download_manager.download_item_format")
    def test_download_item(
        self, mock_download, epub_manager, mock_tracker, download_success, should_mark
    ):
        """Test download marking behavior based on success/failure."""
        mock_download.return_value = download_success

        result = epub_manager.download_item(
            bundle_key="bundle123",
            item_number=1,
            format_name="epub",
            output_dir=Path("/tmp/test"),
        )

        assert result is download_success
        if should_mark:
            mock_tracker.mark_downloaded.assert_called_once()
            call_args = mock_tracker.mark_downloaded.call_args
            assert call_args[1]["file_url"] == "bundle123_1_epub"
            assert call_args[1]["bundle_key"] == "bundle123"
            assert call_args[1]["filename"] == "item_1.epub"
        else:
            mock_tracker.mark_downloaded.assert_not_called()

    @patch("humble_tools.core.download_manager.download_item_format")
    def test_download_item_creates_output_directory(self, mock_download, epub_manager):
        """Test that output directory is created if it doesn't exist."""
        mock_download.return_value = True

        # Use a temporary path that doesn't exist
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            output_path = Path("/tmp/nonexistent/dir")
            epub_manager.download_item(
                bundle_key="bundle",
                item_number=1,
                format_name="epub",
                output_dir=output_path,
            )

            # Verify mkdir was called with correct arguments
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("humble_tools.core.download_manager.download_item_format")
    def test_download_item_with_uppercase_format(
        self, mock_download, epub_manager, mock_tracker
    ):
        """Test that format name is handled correctly regardless of case."""
        mock_download.return_value = True

        epub_manager.download_item(
            bundle_key="bundle",
            item_number=1,
            format_name="EPUB",
            output_dir=Path("/tmp/test"),
        )

        # Check that file_id uses lowercase
        call_args = mock_tracker.mark_downloaded.call_args
        assert call_args[1]["file_url"] == "bundle_1_epub"
        assert call_args[1]["filename"] == "item_1.epub"


class TestDownloadManagerGetBundleStats:
    """Tests for get_bundle_stats method."""

    def test_get_bundle_stats_calls_tracker(self):
        """Test that get_bundle_stats delegates to tracker."""
        mock_tracker = Mock()
        mock_tracker.get_bundle_stats.return_value = {
            "downloaded": 2,
            "remaining": 1,
            "total": 3,
        }

        manager = DownloadManager(tracker=mock_tracker)
        stats = manager.get_bundle_stats("bundle123")

        # Verify tracker was called with bundle_key only
        mock_tracker.get_bundle_stats.assert_called_once_with("bundle123")

        assert stats["total"] == 3
        assert stats["downloaded"] == 2
        assert stats["remaining"] == 1
