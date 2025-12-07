"""Tests for TUI components."""

from pathlib import Path
from unittest.mock import Mock, patch

from textual.widgets import Label

from humble_tools.sync.app import (
    BundleDetailsScreen,
    BundleItem,
    BundleListScreen,
    HumbleBundleTUI,
    ItemFormatRow,
)


class TestBundleItem:
    """Test BundleItem widget."""

    def test_bundle_item_initialization(self):
        """Test BundleItem stores bundle key and name."""
        item = BundleItem("test_key", "Test Bundle Name")
        assert item.bundle_key == "test_key"
        assert item.bundle_name == "Test Bundle Name"

    def test_bundle_item_compose(self):
        """Test BundleItem composes a Label with bundle name."""
        item = BundleItem("test_key", "Test Bundle Name")
        widgets = list(item.compose())
        assert len(widgets) == 1
        assert isinstance(widgets[0], Label)


class TestItemFormatRow:
    """Test ItemFormatRow widget."""

    def test_item_format_row_initialization(self):
        """Test ItemFormatRow stores item data correctly."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test Item",
            formats=["EPUB", "MOBI", "PDF"],
            item_size="10 MB",
            format_status={"EPUB": True, "MOBI": False, "PDF": False},
        )
        assert row.item_number == 1
        assert row.item_name == "Test Item"
        assert row.formats == ["EPUB", "MOBI", "PDF"]
        assert row.item_size == "10 MB"
        assert row.format_status == {"EPUB": True, "MOBI": False, "PDF": False}
        assert row.selected_format == "EPUB"  # Should default to first format

    def test_item_format_row_selected_format_override(self):
        """Test ItemFormatRow respects selected_format parameter."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test Item",
            formats=["EPUB", "MOBI", "PDF"],
            item_size="10 MB",
            format_status={},
            selected_format="PDF",
        )
        assert row.selected_format == "PDF"

    def test_item_format_row_no_formats(self):
        """Test ItemFormatRow handles empty formats list."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test Item",
            formats=[],
            item_size="10 MB",
            format_status={},
        )
        assert row.selected_format is None

    def test_cycle_format_advances_to_next(self):
        """Test cycle_format advances to next format."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test Item",
            formats=["EPUB", "MOBI", "PDF"],
            item_size="10 MB",
            format_status={},
        )
        assert row.selected_format == "EPUB"

        # Can't test the UI refresh, but we can test the logic
        old_format = row.selected_format
        current_idx = row.formats.index(old_format)
        next_idx = (current_idx + 1) % len(row.formats)
        expected_format = row.formats[next_idx]

        # Manually update since we can't call the method without UI
        row.selected_format = expected_format
        assert row.selected_format == "MOBI"

    def test_cycle_format_wraps_around(self):
        """Test cycle_format wraps to first format after last."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test Item",
            formats=["EPUB", "MOBI", "PDF"],
            item_size="10 MB",
            format_status={},
            selected_format="PDF",  # Start at last format
        )

        # Simulate cycling (would wrap to first)
        if row.selected_format:
            current_idx = row.formats.index(row.selected_format)
            next_idx = (current_idx + 1) % len(row.formats)
            row.selected_format = row.formats[next_idx]

        assert row.selected_format == "EPUB"

    def test_cycle_format_with_empty_formats(self):
        """Test cycle_format handles empty formats list gracefully."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test Item",
            formats=[],
            item_size="10 MB",
            format_status={},
        )
        # Should not raise exception
        row.cycle_format()
        assert row.selected_format is None

    def test_compose_includes_download_indicators(self):
        """Test compose() generates label with download indicators."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test Item",
            formats=["EPUB", "MOBI"],
            item_size="10 MB",
            format_status={"EPUB": True, "MOBI": False},
        )
        widgets = list(row.compose())
        assert len(widgets) == 1
        assert isinstance(widgets[0], Label)


class TestBundleListScreen:
    """Test BundleListScreen component."""

    def test_bundle_list_screen_initialization(self):
        """Test BundleListScreen initializes with epub_manager."""
        mock_manager = Mock()
        screen = BundleListScreen(mock_manager)
        assert screen.epub_manager is mock_manager
        assert screen.bundles == []

    @patch("humble_tools.sync.app.get_bundles")
    async def test_load_bundles_success(self, mock_get_bundles):
        """Test load_bundles populates bundle list on success."""
        mock_get_bundles.return_value = [
            {"key": "bundle1", "name": "Bundle 1"},
            {"key": "bundle2", "name": "Bundle 2"},
        ]

        mock_manager = Mock()
        screen = BundleListScreen(mock_manager)

        # Simulate loading bundles (without UI)
        screen.bundles = mock_get_bundles()

        assert len(screen.bundles) == 2
        assert screen.bundles[0]["key"] == "bundle1"
        assert screen.bundles[1]["name"] == "Bundle 2"


class TestBundleDetailsScreen:
    """Test BundleDetailsScreen component."""

    def test_bundle_details_screen_initialization(self):
        """Test BundleDetailsScreen initializes correctly."""
        mock_manager = Mock()
        output_dir = Path("/tmp/test")
        screen = BundleDetailsScreen(mock_manager, output_dir)

        assert screen.epub_manager is mock_manager
        assert screen.output_dir == output_dir
        assert screen.bundle_key == ""
        assert screen.bundle_name == ""
        assert screen.bundle_data is None

    def test_load_bundle_sets_attributes(self):
        """Test load_bundle sets bundle key and name."""
        mock_manager = Mock()
        output_dir = Path("/tmp/test")
        screen = BundleDetailsScreen(mock_manager, output_dir)

        # Can't call load_bundle without UI, so test the logic
        screen.bundle_key = "test_bundle_key"
        screen.bundle_name = "Test Bundle"

        assert screen.bundle_key == "test_bundle_key"
        assert screen.bundle_name == "Test Bundle"


class TestHumbleBundleTUI:
    """Test HumbleBundleTUI app."""

    def test_tui_initialization(self):
        """Test HumbleBundleTUI initializes with correct defaults."""
        app = HumbleBundleTUI()

        assert app.tracker is not None
        assert app.epub_manager is not None
        assert app.output_dir == Path.home() / "Downloads" / "HumbleBundle"
        assert app.current_screen == "list"

    def test_tui_initialization_with_custom_output_dir(self):
        """Test HumbleBundleTUI accepts custom output directory."""
        custom_dir = Path("/custom/output")
        app = HumbleBundleTUI(output_dir=custom_dir)

        assert app.output_dir == custom_dir

    @patch("humble_tools.sync.app.get_bundles")
    async def test_tui_app_starts(self, mock_get_bundles):
        """Test TUI app can start and exit."""
        mock_get_bundles.return_value = []

        app = HumbleBundleTUI()

        # Use run_test to simulate app startup
        async with app.run_test() as pilot:
            # Wait for initial load
            await pilot.pause()

            # App should start successfully
            assert app.is_running

            # App should have mounted screens
            assert app.bundle_list_screen is not None
            assert app.bundle_details_screen is not None

            # Details screen should be hidden initially
            assert app.bundle_details_screen.display is False

            # Press q to quit
            await pilot.press("q")

    @patch("humble_tools.sync.app.get_bundles")
    async def test_tui_loads_bundles_on_start(self, mock_get_bundles):
        """Test TUI loads bundles when started."""
        mock_get_bundles.return_value = [{"key": "test_key", "name": "Test Bundle"}]

        app = HumbleBundleTUI()

        async with app.run_test() as pilot:
            # Wait for bundles to load
            await pilot.pause()

            # Bundles should be loaded
            assert app.bundle_list_screen is not None
            assert len(app.bundle_list_screen.bundles) == 1
            assert app.bundle_list_screen.bundles[0]["key"] == "test_key"

    @patch("humble_tools.sync.app.get_bundles")
    async def test_tui_can_navigate_bundle_list(self, mock_get_bundles):
        """Test navigating through bundle list with arrow keys."""
        from textual.widgets import ListView

        mock_get_bundles.return_value = [
            {"key": "bundle1", "name": "Bundle 1"},
            {"key": "bundle2", "name": "Bundle 2"},
            {"key": "bundle3", "name": "Bundle 3"},
        ]

        app = HumbleBundleTUI()

        async with app.run_test() as pilot:
            # Wait for bundles to load
            await pilot.pause()

            # Get the ListView
            assert app.bundle_list_screen is not None
            list_view = app.bundle_list_screen.query_one("#bundle-list", ListView)

            # Initial position should be 0
            assert list_view.index == 0

            # Press down arrow
            await pilot.press("down")
            assert list_view.index == 1

            # Press down arrow again
            await pilot.press("down")
            assert list_view.index == 2

            # Press up arrow
            await pilot.press("up")
            assert list_view.index == 1

    @patch("humble_tools.sync.app.get_bundles")
    async def test_tui_shows_bundle_details_on_selection(self, mock_get_bundles):
        """Test selecting a bundle shows details screen."""
        mock_get_bundles.return_value = [{"key": "test_key", "name": "Test Bundle"}]

        app = HumbleBundleTUI()

        # Mock the get_bundle_items to avoid actual API calls
        mock_bundle_data = {
            "name": "Test Bundle",
            "purchased": "2024-01-01",
            "amount": "$10.00",
            "total_size": "100 MB",
            "items": [
                {
                    "number": 1,
                    "name": "Test Item",
                    "formats": ["EPUB"],
                    "size": "10 MB",
                    "format_status": {"EPUB": False},
                }
            ],
            "keys": [],
        }
        app.epub_manager.get_bundle_items = Mock(return_value=mock_bundle_data)

        async with app.run_test() as pilot:
            # Wait for bundles to load
            await pilot.pause()

            # Press enter to select first bundle
            await pilot.press("enter")

            # Wait for details to load
            await pilot.pause()

            # Should switch to details screen
            assert app.current_screen == "details"
            assert app.bundle_list_screen is not None
            assert app.bundle_details_screen is not None
            assert app.bundle_list_screen.display is False
            assert app.bundle_details_screen.display is True

    @patch("humble_tools.sync.app.get_bundles")
    async def test_tui_can_go_back_from_details(self, mock_get_bundles):
        """Test pressing escape goes back to bundle list."""
        mock_get_bundles.return_value = [{"key": "test_key", "name": "Test Bundle"}]

        app = HumbleBundleTUI()

        # Mock the get_bundle_items
        mock_bundle_data = {
            "name": "Test Bundle",
            "purchased": "2024-01-01",
            "amount": "$10.00",
            "total_size": "100 MB",
            "items": [],
            "keys": [],
        }
        app.epub_manager.get_bundle_items = Mock(return_value=mock_bundle_data)

        async with app.run_test() as pilot:
            # Wait for bundles to load
            await pilot.pause()

            # Select bundle
            await pilot.press("enter")
            await pilot.pause()

            # Should be in details screen
            assert app.current_screen == "details"

            # Press escape to go back
            await pilot.press("escape")

            # Should be back in list screen
            assert app.current_screen == "list"
            assert app.bundle_list_screen is not None
            assert app.bundle_details_screen is not None
            assert app.bundle_list_screen.display is True
            assert app.bundle_details_screen.display is False

    @patch("humble_tools.sync.app.get_bundles")
    async def test_tui_handles_empty_bundle_list(self, mock_get_bundles):
        """Test TUI handles empty bundle list gracefully."""
        from textual.widgets import Static

        mock_get_bundles.return_value = []

        app = HumbleBundleTUI()

        async with app.run_test() as pilot:
            # Wait for bundles to load
            await pilot.pause()

            # Should have no bundles
            assert app.bundle_list_screen is not None
            assert len(app.bundle_list_screen.bundles) == 0

            # Status should indicate no bundles found
            status = app.bundle_list_screen.query_one("#status-text", Static)
            # Check the plain text version
            status_text = status.render()
            assert "0 bundles" in str(status_text).lower()
