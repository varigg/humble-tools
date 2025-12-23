"""pytest configuration and shared fixtures."""

from unittest.mock import Mock, patch

import pytest
from humble_tools.core.download_manager import DownloadManager


@pytest.fixture
def mock_tracker():
    """Create a mock tracker for testing."""
    return Mock()


@pytest.fixture
def download_manager(mock_tracker):
    """Create a DownloadManager with a mock tracker."""
    return DownloadManager(tracker=mock_tracker)


@pytest.fixture
def mock_download_manager():
    """Shared mock download manager with common return values."""
    manager = Mock()
    manager.download_item = Mock(return_value=True)
    manager.get_bundle_items = Mock(
        return_value={
            "name": "Test Bundle",
            "purchased": "2024-01-01",
            "amount": "$10.00",
            "total_size": "100 MB",
            "items": [],
            "keys": [],
        }
    )
    return manager


def create_bundle_data(
    name="Test Bundle",
    items=None,
    keys=None,
    purchased="2024-01-01",
    amount="$10.00",
    total_size="100 MB",
):
    """Factory for creating test bundle data."""
    return {
        "name": name,
        "purchased": purchased,
        "amount": amount,
        "total_size": total_size,
        "items": items or [],
        "keys": keys or [],
    }


# ============================================================================
# Integration Test Fixtures (Phase 7b)
# ============================================================================
# ============================================================================


@pytest.fixture
def mock_get_bundles():
    """Mock get_bundles function for integration tests."""
    with patch("humble_tools.sync.app.get_bundles") as mock:
        mock.return_value = [
            {"key": "bundle_1", "name": "Test Bundle 1"},
            {"key": "bundle_2", "name": "Test Bundle 2"},
        ]
        yield mock


@pytest.fixture
def mock_bundle_with_items():
    """Mock bundle data with items for integration tests."""
    return {
        "purchased": "2024-01-01",
        "amount": "$15.00",
        "total_size": "100 MB",
        "items": [
            {
                "number": 1,
                "name": "Test Book 1",
                "formats": ["PDF", "EPUB"],
                "size": "10 MB",
                "format_status": {"PDF": False, "EPUB": False},
            },
            {
                "number": 2,
                "name": "Test Book 2",
                "formats": ["EPUB", "MOBI"],
                "size": "15 MB",
                "format_status": {"EPUB": False, "MOBI": False},
            },
            {
                "number": 3,
                "name": "Test Book 3",
                "formats": ["PDF"],
                "size": "20 MB",
                "format_status": {"PDF": False},
            },
        ],
        "keys": [],
    }


@pytest.fixture
def mock_bundle_with_keys():
    """Mock bundle data with keys instead of items."""
    return {
        "purchased": "2024-01-01",
        "amount": "$10.00",
        "total_size": "0 MB",
        "items": [],
        "keys": [
            {
                "number": 1,
                "name": "Steam Key",
                "key": "XXXXX-XXXXX-XXXXX",
                "redeemed": False,
            },
            {
                "number": 2,
                "name": "Epic Key",
                "key": "YYYYY-YYYYY-YYYYY",
                "redeemed": True,
            },
        ],
    }
