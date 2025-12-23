"""Integration tests for screen transitions."""

from unittest.mock import Mock, patch

import pytest

from humble_tools.sync.app import HumbleBundleTUI


class TestScreenNavigation:
    """Test screen navigation workflows."""

    @pytest.mark.asyncio
    async def test_bundle_to_details_and_back(
        self,
        mock_get_bundles,
        mock_bundle_with_items,
    ):
        """Test complete navigation cycle: bundles → details → bundles."""
        app = HumbleBundleTUI()
        app.download_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Should start on list screen
            assert app.current_screen == "list"

            # Navigate to details
            await pilot.press("enter")
            await pilot.pause()
            assert app.current_screen == "details"

            # Verify bundle data loaded with correct item count
            details_screen = app.bundle_details_screen
            assert details_screen is not None
            assert len(details_screen.bundle_data["items"]) == 3

            # Navigate back
            await pilot.press("escape")
            await pilot.pause()
            assert app.current_screen == "list"

    @pytest.mark.asyncio
    async def test_bundle_with_only_keys(
        self,
        mock_get_bundles,
        mock_bundle_with_keys,
    ):
        """Test bundle with only keys (no downloadable items) loads correctly."""
        app = HumbleBundleTUI()
        app.download_manager.get_bundle_items = Mock(return_value=mock_bundle_with_keys)

        async with app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()

            # Should navigate successfully
            assert app.current_screen == "details"

            # Should have keys but no items
            details_screen = app.bundle_details_screen
            assert len(details_screen.bundle_data["keys"]) == 2
            assert len(details_screen.bundle_data["items"]) == 0

    @pytest.mark.asyncio
    async def test_empty_bundle_list_handles_gracefully(self):
        """Test empty bundle list doesn't crash on navigation."""
        with patch("humble_tools.sync.app.get_bundles") as mock:
            mock.return_value = []

            app = HumbleBundleTUI()

            async with app.run_test() as pilot:
                await pilot.pause()

                # Should show list screen even if empty
                assert app.current_screen == "list"

                # Pressing enter should not crash
                await pilot.press("enter")
                await pilot.pause()

                # Should remain on list screen
                assert app.current_screen == "list"
