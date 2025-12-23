"""Tests for display module."""

from io import StringIO
from unittest.mock import patch

import pytest

from humble_tools.track.display import display_bundle_status


class TestDisplayBundleStatus:
    """Tests for display_bundle_status function."""

    @pytest.mark.parametrize(
        "stats,description",
        [
            ({"downloaded": 5, "remaining": 10, "total": 15}, "with known total"),
            ({"downloaded": 5, "remaining": None, "total": None}, "when total is None"),
            ({"downloaded": 0, "remaining": 0, "total": 0}, "with zero total"),
            ({}, "with empty stats dict"),
        ],
    )
    def test_display_bundle_status(self, stats, description):
        """Test displaying bundle status {description}."""
        # Should not raise any exceptions
        with patch("sys.stdout", new=StringIO()):
            display_bundle_status("Test Bundle", stats)
