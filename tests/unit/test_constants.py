"""Unit tests for constants module (Phase 2)."""

from pathlib import Path

from humble_tools.sync.constants import (
    DEFAULT_OUTPUT_DIR,
    Colors,
    StatusSymbols,
    WidgetIds,
)


class TestConstants:
    """Test module-level constants."""

    def test_default_output_dir(self):
        """Test default output directory is a Path."""
        assert isinstance(DEFAULT_OUTPUT_DIR, Path)
        assert "HumbleBundle" in str(DEFAULT_OUTPUT_DIR)


class TestWidgetIds:
    """Test WidgetIds class."""

    def test_bundle_list_screen_ids(self):
        """Test bundle list screen widget IDs are defined."""
        assert hasattr(WidgetIds, "BUNDLE_LIST")
        assert hasattr(WidgetIds, "STATUS_TEXT")
        assert hasattr(WidgetIds, "SCREEN_HEADER")

        assert isinstance(WidgetIds.BUNDLE_LIST, str)
        assert isinstance(WidgetIds.STATUS_TEXT, str)
        assert isinstance(WidgetIds.SCREEN_HEADER, str)

    def test_bundle_details_screen_ids(self):
        """Test bundle details screen widget IDs are defined."""
        assert hasattr(WidgetIds, "BUNDLE_HEADER")
        assert hasattr(WidgetIds, "BUNDLE_METADATA")
        assert hasattr(WidgetIds, "ITEMS_LIST")
        assert hasattr(WidgetIds, "DETAILS_STATUS")
        assert hasattr(WidgetIds, "NOTIFICATION_AREA")

        assert isinstance(WidgetIds.BUNDLE_HEADER, str)
        assert isinstance(WidgetIds.BUNDLE_METADATA, str)
        assert isinstance(WidgetIds.ITEMS_LIST, str)
        assert isinstance(WidgetIds.DETAILS_STATUS, str)
        assert isinstance(WidgetIds.NOTIFICATION_AREA, str)

    def test_widget_ids_are_unique(self):
        """Test all widget IDs are unique."""
        ids = [
            WidgetIds.BUNDLE_LIST,
            WidgetIds.STATUS_TEXT,
            WidgetIds.SCREEN_HEADER,
            WidgetIds.BUNDLE_HEADER,
            WidgetIds.BUNDLE_METADATA,
            WidgetIds.ITEMS_LIST,
            WidgetIds.DETAILS_STATUS,
            WidgetIds.NOTIFICATION_AREA,
        ]
        assert len(ids) == len(set(ids)), "Widget IDs should be unique"


class TestStatusSymbols:
    """Test StatusSymbols class."""

    def test_all_status_symbols_defined(self):
        """Test all status symbols are defined."""
        assert hasattr(StatusSymbols, "DOWNLOADED")
        assert hasattr(StatusSymbols, "DOWNLOADING")
        assert hasattr(StatusSymbols, "QUEUED")
        assert hasattr(StatusSymbols, "NOT_DOWNLOADED")
        assert hasattr(StatusSymbols, "FAILED")

    def test_status_symbols_values(self):
        """Test status symbols have expected values."""
        assert StatusSymbols.DOWNLOADED == "✓"
        assert StatusSymbols.DOWNLOADING == "⏳"
        assert StatusSymbols.QUEUED == "🕒"
        assert StatusSymbols.NOT_DOWNLOADED == " "
        assert StatusSymbols.FAILED == "✗"

    def test_status_symbols_are_unique(self):
        """Test all status symbols are unique (except intentional duplicates)."""
        symbols = [
            StatusSymbols.DOWNLOADED,
            StatusSymbols.DOWNLOADING,
            StatusSymbols.QUEUED,
            StatusSymbols.FAILED,
            # Exclude NOT_DOWNLOADED as it's a space and might overlap
        ]
        assert len(symbols) == len(set(symbols)), "Status symbols should be unique"


class TestColors:
    """Test Colors class."""

    def test_all_colors_defined(self):
        """Test all color names are defined."""
        assert hasattr(Colors, "SUCCESS")
        assert hasattr(Colors, "ERROR")
        assert hasattr(Colors, "WARNING")
        assert hasattr(Colors, "INFO")
        assert hasattr(Colors, "SELECTED")
        assert hasattr(Colors, "MUTED")

    def test_color_values(self):
        """Test colors have expected values."""
        assert Colors.SUCCESS == "green"
        assert Colors.ERROR == "red"
        assert Colors.WARNING == "yellow"
        assert Colors.INFO == "blue"
        assert Colors.SELECTED == "bold cyan"
        assert Colors.MUTED == "text-muted"
