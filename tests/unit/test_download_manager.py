"""Tests for download_manager module.

Test Coverage:
- File ID creation with various bundle keys and formats
- Download manager initialization with and without tracker
- Bundle item retrieval with download status tracking
- Download operations and tracker integration
- Output directory creation
- Error handling for download and API failures
- Bundle statistics delegation to tracker

Performance: All tests are fast (< 0.5s each)
Dependencies: Mocks humble_wrapper functions and tracker
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from humble_tools.core.download_manager import DownloadManager, _create_file_id

from tests.conftest import create_bundle_data


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
            (None, True),  # with None explicitly (default behavior)
        ],
    )
    def test_init(self, tracker_arg, should_create):
        """Test initialization with and without tracker."""
        manager = DownloadManager(tracker=tracker_arg)
        if should_create:
            assert manager.tracker is not None
        else:
            assert manager.tracker == tracker_arg


class TestDownloadManagerGetBundleItems:
    """Tests for get_bundle_items method."""

    @patch("humble_tools.core.download_manager.get_bundle_details")
    @patch("humble_tools.core.download_manager.parse_bundle_details")
    def test_get_bundle_items_adds_download_status(self, mock_parse, mock_get_details):
        """Test that download status is added to each item format."""
        # Setup mocks
        mock_get_details.return_value = "raw details"
        mock_parse.return_value = create_bundle_data(
            name="Test Bundle",
            amount="$10",
            total_size="100 MiB",
            items=[
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
        )

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


class TestDownloadManagerDownloadItem:
    """Tests for download_item method."""

    @pytest.mark.parametrize(
        "download_success,should_mark",
        [
            (True, True),  # successful download
            (False, False),  # failed download
        ],
    )
    @patch("humble_tools.core.download_manager.validate_output_directory")
    @patch("humble_tools.core.download_manager.download_item_format")
    def test_download_item(
        self,
        mock_download,
        mock_validate,
        download_manager,
        mock_tracker,
        download_success,
        should_mark,
    ):
        """Test download marking behavior based on success/failure."""
        mock_download.return_value = download_success

        result = download_manager.download_item(
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

    @patch("humble_tools.core.download_manager.validate_output_directory")
    @patch("humble_tools.core.download_manager.download_item_format")
    def test_download_item_creates_output_directory(
        self, mock_download, mock_validate, download_manager
    ):
        """Test that output directory is created if it doesn't exist."""
        mock_download.return_value = True

        # Use a temporary path that doesn't exist
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            output_path = Path("/tmp/nonexistent/dir")
            download_manager.download_item(
                bundle_key="bundle",
                item_number=1,
                format_name="epub",
                output_dir=output_path,
            )

            # Verify mkdir was called with correct arguments
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestDownloadManagerErrorHandling:
    """Tests for error handling in download operations."""

    @patch("humble_tools.core.download_manager.validate_output_directory")
    @patch("humble_tools.core.download_manager.download_item_format")
    def test_download_item_propagates_exceptions(
        self, mock_download, mock_validate, download_manager, mock_tracker
    ):
        """Test download propagates exceptions and doesn't mark tracker on error."""
        mock_download.side_effect = OSError("Network connection failed")

        # Should propagate the exception
        with pytest.raises(IOError, match="Network connection failed"):
            download_manager.download_item(
                bundle_key="bundle123",
                item_number=1,
                format_name="epub",
                output_dir=Path("/tmp/test"),
            )

        # Tracker should NOT be marked as downloaded on error
        mock_tracker.mark_downloaded.assert_not_called()

    @patch("humble_tools.core.download_manager.get_bundle_details")
    @patch("humble_tools.core.download_manager.parse_bundle_details")
    def test_get_bundle_items_propagates_parse_error(self, mock_parse, mock_get_details):
        """Test get_bundle_items propagates parsing errors."""
        mock_get_details.return_value = "raw details"
        mock_parse.side_effect = ValueError("Invalid bundle format")

        manager = DownloadManager(tracker=Mock())

        with pytest.raises(ValueError, match="Invalid bundle format"):
            manager.get_bundle_items("bundle123")

    @patch("humble_tools.core.download_manager.get_bundle_details")
    def test_get_bundle_items_propagates_api_error(self, mock_get_details):
        """Test get_bundle_items propagates API errors."""
        mock_get_details.side_effect = RuntimeError("API unavailable")

        manager = DownloadManager(tracker=Mock())

        with pytest.raises(RuntimeError, match="API unavailable"):
            manager.get_bundle_items("bundle123")
