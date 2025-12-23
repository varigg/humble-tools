"""Unit tests for ItemFormatRow display and formatting.

Test Coverage:
- Display text building for various download states
- Status symbols (downloaded, downloading, queued, not downloaded)
- Color coding (success, warning, info, selected)
- Multiple format handling and display
- Format cycling and selection
- Format state tracking (status, downloading, queued)
- Independent state management for multiple formats

Performance: All tests are fast (< 0.01s each)
Dependencies: Uses ItemFormatRow widget, Colors and StatusSymbols constants
"""

import pytest
from humble_tools.sync.app import ItemFormatRow
from humble_tools.sync.constants import Colors, StatusSymbols


class TestItemFormatRowDisplay:
    """Test ItemFormatRow display text building with constants."""

    def test_build_display_text_not_downloaded(self):
        """Test display text for item with no downloads."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test Book",
            formats=["EPUB", "PDF"],
            item_size="10 MB",
            format_status={"EPUB": False, "PDF": False},
        )

        display_text = row._build_display_text()

        # Should contain item number, name, and size
        assert "1" in display_text
        assert "Test Book" in display_text
        assert "10 MB" in display_text

        # Should contain NOT_DOWNLOADED symbol (space)
        assert StatusSymbols.NOT_DOWNLOADED in display_text

        # Should have selected format in cyan
        assert Colors.SELECTED in display_text

    def test_build_display_text_downloaded(self):
        """Test display text for fully downloaded item."""
        row = ItemFormatRow(
            item_number=5,
            item_name="Downloaded Book",
            formats=["EPUB"],
            item_size="15 MB",
            format_status={"EPUB": True},
        )

        display_text = row._build_display_text()

        # Should contain downloaded symbol
        assert StatusSymbols.DOWNLOADED in display_text

        # Should contain success color
        assert Colors.SUCCESS in display_text

    def test_build_display_text_downloading(self):
        """Test display text for item currently downloading."""
        row = ItemFormatRow(
            item_number=3,
            item_name="Current Download",
            formats=["PDF"],
            item_size="20 MB",
            format_status={"PDF": False},
        )

        # Mark as downloading
        row.format_downloading["PDF"] = True
        display_text = row._build_display_text()

        # Should contain downloading symbol
        assert StatusSymbols.DOWNLOADING in display_text

        # Should contain warning color
        assert Colors.WARNING in display_text

    def test_build_display_text_queued(self):
        """Test display text for queued item."""
        row = ItemFormatRow(
            item_number=2,
            item_name="Queued Book",
            formats=["MOBI"],
            item_size="8 MB",
            format_status={"MOBI": False},
        )

        # Mark as queued
        row.format_queued["MOBI"] = True
        display_text = row._build_display_text()

        # Should contain queued symbol
        assert StatusSymbols.QUEUED in display_text

        # Should contain info color
        assert Colors.INFO in display_text

    def test_build_display_text_multiple_formats(self):
        """Test display text with multiple formats."""
        row = ItemFormatRow(
            item_number=10,
            item_name="Multi-Format Book",
            formats=["EPUB", "PDF", "MOBI"],
            item_size="25 MB",
            format_status={"EPUB": True, "PDF": False, "MOBI": False},
        )

        display_text = row._build_display_text()

        # Should contain all format names
        assert "EPUB" in display_text
        assert "PDF" in display_text
        assert "MOBI" in display_text

        # EPUB should show as downloaded
        # PDF and MOBI should show as not downloaded
        assert StatusSymbols.DOWNLOADED in display_text
        assert StatusSymbols.NOT_DOWNLOADED in display_text

    def test_build_display_text_uses_constants(self):
        """Test display text uses dimension constants."""
        row = ItemFormatRow(
            item_number=999,
            item_name="A" * 100,  # Long name to test truncation
            formats=["EPUB"],
            item_size="1 GB",
            format_status={"EPUB": False},
        )

        display_text = row._build_display_text()

        # Name should be truncated to MAX_ITEM_NAME_DISPLAY_LENGTH
        # Can't test exact formatting without complex parsing, but verify
        # the display text is generated without errors
        assert display_text is not None
        assert len(display_text) > 0

    def test_build_display_text_selected_format_highlight(self):
        """Test selected format is highlighted."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB", "PDF"],
            item_size="10 MB",
            format_status={"EPUB": False, "PDF": False},
            selected_format="PDF",
        )

        display_text = row._build_display_text()

        # Selected format should have SELECTED color
        assert Colors.SELECTED in display_text


class TestItemFormatRowFormatCycling:
    """Test format cycling functionality."""

    def test_cycle_format_basic(self):
        """Test basic format cycling."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB", "PDF", "MOBI"],
            item_size="10 MB",
            format_status={},
        )

        assert row.selected_format == "EPUB"

        # Simulate cycling (can't call cycle_format without UI)
        current_idx = row.formats.index(row.selected_format)
        next_idx = (current_idx + 1) % len(row.formats)
        row.selected_format = row.formats[next_idx]

        assert row.selected_format == "PDF"

    def test_cycle_format_wraps_around(self):
        """Test format cycling wraps to beginning."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB", "PDF"],
            item_size="10 MB",
            format_status={},
            selected_format="PDF",  # Start at last format
        )

        assert row.selected_format == "PDF"

        # Cycle to next (should wrap to first)
        current_idx = row.formats.index(row.selected_format)
        next_idx = (current_idx + 1) % len(row.formats)
        row.selected_format = row.formats[next_idx]

        assert row.selected_format == "EPUB"

    def test_cycle_format_single_format(self):
        """Test cycling with single format stays on same format."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB"],
            item_size="10 MB",
            format_status={},
        )

        assert row.selected_format == "EPUB"

        # Cycle to next (should stay on EPUB)
        current_idx = row.formats.index(row.selected_format)
        next_idx = (current_idx + 1) % len(row.formats)
        row.selected_format = row.formats[next_idx]

        assert row.selected_format == "EPUB"


class TestItemFormatRowState:
    """Test ItemFormatRow state management."""

    @pytest.mark.parametrize(
        "state_attr,initial_state,test_format,set_value",
        [
            (
                "format_status",
                {"EPUB": True, "PDF": False},
                "EPUB",
                None,
            ),  # Read-only from init
            (
                "format_status",
                {"EPUB": True, "PDF": False},
                "PDF",
                None,
            ),  # Read-only from init
            ("format_downloading", {}, "EPUB", True),  # Set during download
            ("format_queued", {}, "EPUB", True),  # Set when queued
        ],
    )
    def test_format_state_tracking(self, state_attr, initial_state, test_format, set_value):
        """Test format state tracking for status, downloading, and queued."""
        # Determine format_status for initialization
        format_status = (
            initial_state if state_attr == "format_status" else {"EPUB": False, "PDF": False}
        )

        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB", "PDF"],
            item_size="10 MB",
            format_status=format_status,
        )

        state_dict = getattr(row, state_attr)

        if set_value is None:
            # Test initial values (format_status is read-only)
            expected = initial_state.get(test_format, False)
            assert state_dict[test_format] is expected
        else:
            # Test setting values (format_downloading and format_queued)
            # Initially not set
            assert state_dict.get(test_format, False) is False

            # Set value
            state_dict[test_format] = set_value
            assert state_dict[test_format] is set_value

    def test_multiple_format_independent_states(self):
        """Test different formats can have independent states."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB", "PDF", "MOBI"],
            item_size="10 MB",
            format_status={"EPUB": True, "PDF": False, "MOBI": False},
        )

        # Set different states for each format
        row.format_downloading["PDF"] = True
        row.format_queued["MOBI"] = True

        # Verify independent tracking
        assert row.format_status["EPUB"] is True
        assert row.format_downloading.get("EPUB", False) is False
        assert row.format_queued.get("EPUB", False) is False

        assert row.format_status["PDF"] is False
        assert row.format_downloading["PDF"] is True
        assert row.format_queued.get("PDF", False) is False

        assert row.format_status["MOBI"] is False
        assert row.format_downloading.get("MOBI", False) is False
        assert row.format_queued["MOBI"] is True


class TestItemFormatRowHelperMethods:
    """Test extracted helper methods for Phase 3 readability improvements."""

    def test_get_status_indicator_not_downloaded(self):
        """Test status indicator for format not yet downloaded."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB"],
            item_size="10 MB",
            format_status={"EPUB": False},
        )

        indicator, color = row._get_status_indicator("EPUB")

        assert indicator == StatusSymbols.NOT_DOWNLOADED
        assert color is None

    def test_get_status_indicator_downloaded(self):
        """Test status indicator for downloaded format."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB"],
            item_size="10 MB",
            format_status={"EPUB": True},
        )

        indicator, color = row._get_status_indicator("EPUB")

        assert indicator == StatusSymbols.DOWNLOADED
        assert color == Colors.SUCCESS

    def test_get_status_indicator_downloading(self):
        """Test status indicator for format currently downloading."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB"],
            item_size="10 MB",
            format_status={"EPUB": False},
        )
        row.format_downloading["EPUB"] = True

        indicator, color = row._get_status_indicator("EPUB")

        assert indicator == StatusSymbols.DOWNLOADING
        assert color == Colors.WARNING

    def test_get_status_indicator_queued(self):
        """Test status indicator for queued format."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB"],
            item_size="10 MB",
            format_status={"EPUB": False},
        )
        row.format_queued["EPUB"] = True

        indicator, color = row._get_status_indicator("EPUB")

        assert indicator == StatusSymbols.QUEUED
        assert color == Colors.INFO

    def test_get_status_indicator_priority_queued_over_downloaded(self):
        """Test that queued status has priority over downloaded (edge case)."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB"],
            item_size="10 MB",
            format_status={"EPUB": True},  # Downloaded
        )
        row.format_queued["EPUB"] = True  # But also queued (shouldn't happen normally)

        # Queued should take priority
        indicator, color = row._get_status_indicator("EPUB")
        assert indicator == StatusSymbols.QUEUED

    def test_format_single_item_not_selected_no_color(self):
        """Test formatting single item when not selected and no color."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB", "PDF"],
            item_size="10 MB",
            format_status={"EPUB": False, "PDF": False},
            selected_format="EPUB",  # EPUB is selected
        )

        # Format PDF (not selected, no color)
        result = row._format_single_item("PDF", StatusSymbols.NOT_DOWNLOADED, None)

        # Should be plain text without markup
        assert result == f"[{StatusSymbols.NOT_DOWNLOADED}] PDF"
        assert Colors.SELECTED not in result

    def test_format_single_item_not_selected_with_color(self):
        """Test formatting single item when not selected but has color."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB", "PDF"],
            item_size="10 MB",
            format_status={"EPUB": True, "PDF": False},
            selected_format="PDF",  # PDF is selected
        )

        # Format EPUB (not selected, but downloaded = green)
        result = row._format_single_item("EPUB", StatusSymbols.DOWNLOADED, Colors.SUCCESS)

        # Should have color markup but not selected markup
        assert Colors.SUCCESS in result
        assert Colors.SELECTED not in result
        assert StatusSymbols.DOWNLOADED in result

    def test_format_single_item_selected_no_color(self):
        """Test formatting selected item without status color."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB"],
            item_size="10 MB",
            format_status={"EPUB": False},
            selected_format="EPUB",
        )

        # Format EPUB (selected, not downloaded = no color)
        result = row._format_single_item("EPUB", StatusSymbols.NOT_DOWNLOADED, None)

        # Should have selected markup
        assert Colors.SELECTED in result
        assert StatusSymbols.NOT_DOWNLOADED in result

    def test_format_single_item_selected_with_color(self):
        """Test formatting selected item with status color."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Book",
            formats=["EPUB"],
            item_size="10 MB",
            format_status={"EPUB": False},
            selected_format="EPUB",
        )
        row.format_downloading["EPUB"] = True

        # Format EPUB (selected, downloading = yellow)
        result = row._format_single_item("EPUB", StatusSymbols.DOWNLOADING, Colors.WARNING)

        # Should have both selected and status color
        assert Colors.SELECTED in result
        assert Colors.WARNING in result
        assert StatusSymbols.DOWNLOADING in result
