"""Integration tests for download lifecycle."""

from unittest.mock import Mock

import pytest
from humble_tools.sync.app import HumbleBundleTUI


class TestDownloadWorkflows:
    """Test complete download workflows with real assertions."""

    @pytest.mark.asyncio
    async def test_download_with_format_selection(
        self,
        mock_get_bundles,
        mock_bundle_with_items,
    ):
        """Test downloading after changing format selection."""
        app = HumbleBundleTUI()
        app.download_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)
        app.download_manager.download_item = Mock(return_value=True)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to details (cursor starts on first item)
            await pilot.press("enter")
            await pilot.pause()

            # Cycle format (from PDF to EPUB)
            await pilot.press("right")
            await pilot.pause()

            # Start download
            await pilot.press("enter")
            await pilot.pause(0.5)

            # Verify download was called
            app.download_manager.download_item.assert_called_once()
            call_args = app.download_manager.download_item.call_args

            # Item 1 has ["PDF", "EPUB"], cycling from PDF -> EPUB
            assert call_args[1]["format_name"] == "EPUB"
            assert call_args[1]["item_number"] == 1

    @pytest.mark.asyncio
    async def test_failed_download_returns_false(
        self,
        mock_get_bundles,
        mock_bundle_with_items,
    ):
        """Test failed download (returns False) is handled without crash."""
        app = HumbleBundleTUI()
        app.download_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)
        app.download_manager.download_item = Mock(return_value=False)  # Fail

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate and attempt download (cursor starts on first item)
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause(0.5)

            # Download should have been attempted
            app.download_manager.download_item.assert_called_once()

            # App should still be running and on details screen
            assert app.is_running
            assert app.current_screen == "details"

    @pytest.mark.asyncio
    async def test_download_exception_handled(
        self,
        mock_get_bundles,
        mock_bundle_with_items,
    ):
        """Test download exception is caught and doesn't crash app."""
        app = HumbleBundleTUI()
        app.download_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)
        app.download_manager.download_item = Mock(side_effect=RuntimeError("Network error"))

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate and attempt download
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause(0.5)

            # Should not crash the app
            assert app.is_running
            assert app.current_screen == "details"

    @pytest.mark.asyncio
    async def test_retry_after_failure(
        self,
        mock_get_bundles,
        mock_bundle_with_items,
    ):
        """Test failed download can be retried successfully."""
        app = HumbleBundleTUI()
        app.download_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)

        # First call fails, second succeeds
        app.download_manager.download_item = Mock(side_effect=[False, True])

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to item (cursor starts on first item)
            await pilot.press("enter")
            await pilot.pause()

            # First attempt (fails)
            await pilot.press("enter")
            await pilot.pause(0.5)

            # Second attempt (succeeds)
            await pilot.press("enter")
            await pilot.pause(0.5)

            # Should have tried twice with success on second
            assert app.download_manager.download_item.call_count == 2

    @pytest.mark.asyncio
    async def test_download_persists_during_navigation(
        self,
        mock_get_bundles,
        mock_bundle_with_items,
    ):
        """Test downloads continue after navigating away from details."""
        app = HumbleBundleTUI()
        app.download_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)
        app.download_manager.download_item = Mock(return_value=True)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to details and start download
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause(0.2)

            # Navigate back to bundle list
            await pilot.press("escape")
            await pilot.pause(0.5)

            # Download should complete even after navigation
            app.download_manager.download_item.assert_called_once()

            # Can navigate back without issues
            await pilot.press("enter")
            await pilot.pause()
            assert app.current_screen == "details"
