"""Tests for concurrent downloads feature."""

import asyncio
from unittest.mock import Mock, patch

from textual.widgets import ListView

from humble_tools.sync.app import HumbleBundleTUI


class TestConcurrentDownloads:
    """Test concurrent downloads behavior."""

    @patch("humble_tools.sync.app.get_bundles")
    async def test_download_then_navigate(self, mock_get_bundles):
        """Test that downloading an item and navigating doesn't crash.
        
        Reproduces the TypeError: BundleDetailsScreen.clear_notification()
        got an unexpected keyword argument 'delay'
        """
        mock_get_bundles.return_value = [{"key": "test_key", "name": "Test Bundle"}]

        app = HumbleBundleTUI()

        # Mock the epub_manager.get_bundle_items to return test data
        mock_bundle_data = {
            "purchased": "2024-01-01",
            "amount": "$10.00",
            "total_size": "100 MB",
            "items": [
                {
                    "number": 1,
                    "name": "Test Item 1",
                    "formats": ["EPUB", "PDF"],
                    "size": "50 MB",
                    "format_status": {"EPUB": False, "PDF": False},
                },
                {
                    "number": 2,
                    "name": "Test Item 2",
                    "formats": ["EPUB"],
                    "size": "30 MB",
                    "format_status": {"EPUB": False},
                },
            ],
            "keys": [],
        }
        app.epub_manager.get_bundle_items = Mock(return_value=mock_bundle_data)

        # Mock download_item to succeed
        app.epub_manager.download_item = Mock(return_value=True)

        async with app.run_test() as pilot:
            # Wait for bundles to load
            await pilot.pause()

            # Select bundle
            await pilot.press("enter")
            await pilot.pause()

            # Should be in details screen
            assert app.current_screen == "details"

            # Press down to move to first item (skip header)
            await pilot.press("down")
            await pilot.pause()

            # Press enter to download the item
            await pilot.press("enter")
            await pilot.pause()

            # Now press down while download is in progress
            # This should not crash with the TypeError about 'delay'
            await pilot.press("down")
            await pilot.pause()

            # Continue navigating
            await pilot.press("up")
            await pilot.pause()

            # The TUI should still be responsive
            assert app.current_screen == "details"

    @patch("humble_tools.sync.app.get_bundles")
    async def test_concurrent_downloads_with_slow_mock(self, mock_get_bundles):
        """Test that multiple items can be downloaded concurrently with slow downloads.
        
        This test:
        1. Mocks a slow download on item 1
        2. Starts downloading item 1
        3. Verifies item 1 shows ⏳ indicator
        4. Navigates to item 2
        5. Starts downloading item 2 while item 1 is still downloading
        6. Verifies both items show ⏳ indicator
        7. Verifies counter shows "Active Downloads: 2/3"
        """
        mock_get_bundles.return_value = [{"key": "test_key", "name": "Test Bundle"}]

        app = HumbleBundleTUI()

        # Mock the epub_manager.get_bundle_items to return test data with 2 items
        mock_bundle_data = {
            "purchased": "2024-01-01",
            "amount": "$10.00",
            "total_size": "100 MB",
            "items": [
                {
                    "number": 1,
                    "name": "Slow Item 1",
                    "formats": ["EPUB"],
                    "size": "50 MB",
                    "format_status": {"EPUB": False},
                },
                {
                    "number": 2,
                    "name": "Fast Item 2",
                    "formats": ["EPUB"],
                    "size": "30 MB",
                    "format_status": {"EPUB": False},
                },
            ],
            "keys": [],
        }
        app.epub_manager.get_bundle_items = Mock(return_value=mock_bundle_data)

        # Create a coroutine function for slow download
        async def slow_download(*args, **kwargs):
            # Simulate a slow download
            await asyncio.sleep(0.5)
            return True

        # Mock download_item to return the coroutine
        app.epub_manager.download_item = Mock(side_effect=slow_download)

        async with app.run_test() as pilot:
            # Wait for bundles to load
            await pilot.pause()

            # Select bundle
            await pilot.press("enter")
            await pilot.pause()

            # Should be in details screen
            assert app.current_screen == "details"

            # Get reference to details screen and items list
            details_screen = app.bundle_details_screen
            assert details_screen is not None
            list_view = details_screen.query_one("#items-list", ListView)

            # After load_details, index is set to 1 (first item, skipping header at 0)
            await pilot.pause(0.5)  # Wait for details to fully load
            
            # Item 1 should be at index 1
            assert list_view.index == 1
            item1 = list_view.children[list_view.index]

            # Download item 1
            await pilot.press("enter")
            # Let the async worker start and update UI
            await pilot.pause(0.5)  # Longer pause to let download initiate

            # Verify item 1 shows downloading indicator (⏳)
            # The format_downloading should be set
            # Check if download started
            is_downloading_1 = item1.format_downloading.get("EPUB", False)
            if not is_downloading_1:
                # If not downloading yet, the @work decorator might not have started the worker
                # This could indicate the issue: downloads aren't truly concurrent
                raise AssertionError(
                    f"Item 1 should show downloading. "
                    f"format_downloading={item1.format_downloading}, "
                    f"active_downloads={details_screen.active_downloads}"
                )

            # Verify counter shows active download
            assert details_screen.active_downloads >= 1, "Should have at least 1 active download"

            # Now navigate to item 2 while item 1 is downloading
            await pilot.press("down")
            await pilot.pause(0.1)

            # Verify we're on item 2 (at index 2)
            assert list_view.index == 2
            item2 = list_view.children[list_view.index]

            # Download item 2
            await pilot.press("enter")
            await pilot.pause(0.5)  # Let second download initiate

            # Verify item 2 also shows downloading indicator
            is_downloading_2 = item2.format_downloading.get("EPUB", False)
            if not is_downloading_2:
                raise AssertionError(
                    f"Item 2 should show downloading. "
                    f"format_downloading={item2.format_downloading}, "
                    f"active_downloads={details_screen.active_downloads}"
                )

            # Verify counter shows 2 active downloads
            assert details_screen.active_downloads == 2, (
                f"Should have 2 active downloads, got {details_screen.active_downloads}"
            )

            # Wait for downloads to complete
            await pilot.pause(1.5)

            # After downloads complete, active_downloads should be back to 0
            assert details_screen.active_downloads == 0, "All downloads should be complete"

