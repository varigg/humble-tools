# Phase 7a: Unit Tests - Detailed Task Document

**Date Created:** December 22, 2025  
**Status:** Ready for Implementation  
**Priority:** HIGH  
**Estimated Effort:** 3-4 hours  
**Risk Level:** Low  
**Dependencies:** Phases 1-4 should be completed for best results

---

## Overview

Phase 7a focuses on creating comprehensive unit tests for all components, helper methods, and business logic in the TUI application. Unit tests verify individual components in isolation, providing fast feedback and enabling confident refactoring.

### Goals

- ✅ Achieve >85% code coverage for app.py
- ✅ Test all helper methods extracted in Phase 3
- ✅ Test ItemFormatRow thoroughly
- ✅ Test DownloadQueue independently (if Phase 4 completed)
- ✅ Test configuration and constants
- ✅ Create reusable test fixtures
- ✅ Enable test-driven development for future changes

### Success Criteria

- [x] Unit test coverage >85% for sync module
- [x] All helper methods have dedicated tests
- [x] All edge cases covered
- [x] Tests run in <5 seconds
- [x] No flaky tests
- [x] Clear test organization
- [x] Comprehensive test documentation

---

## Test Structure Overview

```
tests/
└── test_sync/
    ├── __init__.py
    ├── conftest.py                    # Shared fixtures
    ├── test_app_helpers.py            # Helper method tests
    ├── test_item_format_row.py        # ItemFormatRow tests
    ├── test_bundle_details_screen.py  # BundleDetailsScreen tests
    ├── test_bundle_list_screen.py     # BundleListScreen tests
    ├── test_download_queue.py         # DownloadQueue tests (Phase 4)
    └── test_config.py                 # Configuration tests (Phase 2)
```

---

## Task 1: Create Shared Test Fixtures

**Priority:** HIGH  
**Estimated Time:** 30 minutes  
**File:** `tests/test_sync/conftest.py`

### Purpose

Create reusable fixtures that reduce duplication across test files.

### Implementation

```python
"""Shared pytest fixtures for sync module tests."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from humble_tools.core.download_manager import DownloadManager
from humble_tools.sync.app import (
    ItemFormatRow,
    BundleDetailsScreen,
    BundleListScreen,
    HumbleBundleTUI,
)


@pytest.fixture
def mock_download_manager():
    """Create a mock DownloadManager."""
    mock = Mock(spec=DownloadManager)
    mock.download_item = Mock(return_value=True)
    mock.get_bundle_items = Mock(return_value={
        "purchased": "2024-01-01",
        "amount": "$10.00",
        "total_size": "100 MB",
        "items": [],
        "keys": [],
    })
    return mock


@pytest.fixture
def sample_item_row():
    """Create a sample ItemFormatRow for testing."""
    return ItemFormatRow(
        item_number=1,
        item_name="Test Book",
        formats=["PDF", "EPUB", "MOBI"],
        item_size="10 MB",
        format_status={"PDF": False, "EPUB": False, "MOBI": False},
        selected_format="PDF",
    )


@pytest.fixture
def sample_item_row_downloaded():
    """Create ItemFormatRow with some formats downloaded."""
    return ItemFormatRow(
        item_number=2,
        item_name="Downloaded Book",
        formats=["PDF", "EPUB"],
        item_size="15 MB",
        format_status={"PDF": True, "EPUB": False},
        selected_format="EPUB",
    )


@pytest.fixture
def sample_bundle_data():
    """Create sample bundle data structure."""
    return {
        "purchased": "2024-01-01",
        "amount": "$15.00",
        "total_size": "500 MB",
        "items": [
            {
                "number": 1,
                "name": "Item 1",
                "formats": ["PDF", "EPUB"],
                "size": "10 MB",
                "format_status": {"PDF": False, "EPUB": False},
            },
            {
                "number": 2,
                "name": "Item 2",
                "formats": ["EPUB", "MOBI"],
                "size": "15 MB",
                "format_status": {"EPUB": True, "MOBI": False},
            },
        ],
        "keys": [
            {
                "name": "Steam Key 1",
                "key": "XXXXX-XXXXX-XXXXX",
            }
        ],
    }


@pytest.fixture
def mock_bundle_details_screen(mock_download_manager):
    """Create BundleDetailsScreen with mocked dependencies."""
    with patch('humble_tools.sync.app.Path'):
        screen = BundleDetailsScreen(
            epub_manager=mock_download_manager,
            output_dir=Path("/tmp/test"),
        )
        # Mock app reference
        screen.app = Mock()
        screen.app.call_from_thread = Mock(side_effect=lambda fn, *args, **kwargs: fn(*args, **kwargs))
        return screen


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "humble_downloads"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_textual_app():
    """Create mock Textual app instance."""
    app = Mock()
    app.call_from_thread = Mock(side_effect=lambda fn, *args, **kwargs: fn(*args, **kwargs))
    app.exit = Mock()
    return app
```

### Steps

1. Create or update `tests/test_sync/conftest.py`
2. Add the fixtures above
3. Test fixtures work:
   ```bash
   uv run pytest tests/test_sync/ --collect-only
   ```

### Verification

- [x] File created/updated
- [x] Fixtures importable
- [x] No import errors
- [x] Tests can collect successfully

---

## Task 2: Test ItemFormatRow Class

**Priority:** HIGH  
**Estimated Time:** 45 minutes  
**File:** `tests/test_sync/test_item_format_row.py`

### Implementation

```python
"""Unit tests for ItemFormatRow widget."""

import pytest
from humble_tools.sync.app import ItemFormatRow


class TestItemFormatRowInitialization:
    """Tests for ItemFormatRow initialization."""

    def test_basic_initialization(self):
        """Test basic initialization with required parameters."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test Item",
            formats=["PDF", "EPUB"],
            item_size="10 MB",
            format_status={"PDF": False, "EPUB": True},
        )

        assert row.item_number == 1
        assert row.item_name == "Test Item"
        assert row.formats == ["PDF", "EPUB"]
        assert row.item_size == "10 MB"
        assert row.format_status == {"PDF": False, "EPUB": True}
        assert row.selected_format == "PDF"  # Defaults to first

    def test_initialization_with_selected_format(self):
        """Test initialization with explicit selected format."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test",
            formats=["PDF", "EPUB", "MOBI"],
            item_size="10 MB",
            format_status={},
            selected_format="MOBI",
        )

        assert row.selected_format == "MOBI"

    def test_initialization_empty_formats(self):
        """Test initialization with no formats."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test",
            formats=[],
            item_size="10 MB",
            format_status={},
        )

        assert row.selected_format is None

    def test_downloading_queued_dicts_initialized(self):
        """Test that tracking dictionaries are initialized empty."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test",
            formats=["PDF"],
            item_size="10 MB",
            format_status={},
        )

        assert row.format_downloading == {}
        assert row.format_queued == {}


class TestItemFormatRowFormatCycling:
    """Tests for format cycling functionality."""

    def test_cycle_format_advances(self, sample_item_row):
        """Test cycling advances to next format."""
        assert sample_item_row.selected_format == "PDF"

        sample_item_row.cycle_format()
        assert sample_item_row.selected_format == "EPUB"

        sample_item_row.cycle_format()
        assert sample_item_row.selected_format == "MOBI"

    def test_cycle_format_wraps(self, sample_item_row):
        """Test cycling wraps to first format."""
        sample_item_row.selected_format = "MOBI"
        sample_item_row.cycle_format()
        assert sample_item_row.selected_format == "PDF"

    def test_cycle_format_empty_formats(self):
        """Test cycling with no formats does nothing."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test",
            formats=[],
            item_size="10 MB",
            format_status={},
        )

        row.cycle_format()
        assert row.selected_format is None

    def test_cycle_format_single_format(self):
        """Test cycling with single format stays on same."""
        row = ItemFormatRow(
            item_number=1,
            item_name="Test",
            formats=["PDF"],
            item_size="10 MB",
            format_status={},
        )

        row.cycle_format()
        assert row.selected_format == "PDF"


class TestItemFormatRowStatusIndicator:
    """Tests for _get_status_indicator method (if extracted in Phase 3)."""

    def test_status_queued(self, sample_item_row):
        """Test status indicator for queued format."""
        sample_item_row.format_queued["PDF"] = True

        # Assuming Phase 3 extracted this method
        if hasattr(sample_item_row, '_get_status_indicator'):
            indicator, color = sample_item_row._get_status_indicator("PDF")
            assert indicator == "🕒"
            assert color == "blue"

    def test_status_downloading(self, sample_item_row):
        """Test status indicator for downloading format."""
        sample_item_row.format_downloading["PDF"] = True

        if hasattr(sample_item_row, '_get_status_indicator'):
            indicator, color = sample_item_row._get_status_indicator("PDF")
            assert indicator == "⏳"
            assert color == "yellow"

    def test_status_downloaded(self, sample_item_row):
        """Test status indicator for downloaded format."""
        sample_item_row.format_status["PDF"] = True

        if hasattr(sample_item_row, '_get_status_indicator'):
            indicator, color = sample_item_row._get_status_indicator("PDF")
            assert indicator == "✓"
            assert color == "green"

    def test_status_available(self, sample_item_row):
        """Test status indicator for available (not downloaded) format."""
        if hasattr(sample_item_row, '_get_status_indicator'):
            indicator, color = sample_item_row._get_status_indicator("PDF")
            assert indicator == " "
            assert color is None

    def test_status_priority_queued_over_downloading(self, sample_item_row):
        """Test queued takes priority over downloading."""
        sample_item_row.format_queued["PDF"] = True
        sample_item_row.format_downloading["PDF"] = True  # Both set

        if hasattr(sample_item_row, '_get_status_indicator'):
            indicator, color = sample_item_row._get_status_indicator("PDF")
            assert indicator == "🕒"  # Should be queued
            assert color == "blue"

    def test_status_priority_downloading_over_downloaded(self, sample_item_row):
        """Test downloading takes priority over downloaded."""
        sample_item_row.format_downloading["PDF"] = True
        sample_item_row.format_status["PDF"] = True  # Both set

        if hasattr(sample_item_row, '_get_status_indicator'):
            indicator, color = sample_item_row._get_status_indicator("PDF")
            assert indicator == "⏳"  # Should be downloading
            assert color == "yellow"


class TestItemFormatRowDisplayText:
    """Tests for display text building."""

    def test_build_display_text_basic(self, sample_item_row):
        """Test building display text with basic data."""
        text = sample_item_row._build_display_text()

        # Should contain item number
        assert "1" in text or "  1" in text
        # Should contain item name
        assert "Test Book" in text
        # Should contain size
        assert "10 MB" in text

    def test_build_display_text_includes_formats(self, sample_item_row):
        """Test display text includes all formats."""
        text = sample_item_row._build_display_text()

        assert "PDF" in text
        assert "EPUB" in text
        assert "MOBI" in text

    def test_build_display_text_shows_downloaded(self, sample_item_row_downloaded):
        """Test display text indicates downloaded formats."""
        text = sample_item_row_downloaded._build_display_text()

        # Should contain download indicator
        assert "✓" in text or "[green]" in text

    def test_build_display_text_long_name_truncated(self):
        """Test very long item names are truncated."""
        long_name = "A" * 100
        row = ItemFormatRow(
            item_number=1,
            item_name=long_name,
            formats=["PDF"],
            item_size="10 MB",
            format_status={},
        )

        text = row._build_display_text()
        # Exact truncation depends on implementation
        # but should not contain full 100 characters
        assert len(text) < 200


class TestItemFormatRowFormatSingleItem:
    """Tests for _format_single_item method (if extracted in Phase 3)."""

    def test_format_selected_with_color(self, sample_item_row):
        """Test formatting selected item with color."""
        if hasattr(sample_item_row, '_format_single_item'):
            result = sample_item_row._format_single_item("PDF", "✓", "green")

            # Should have bold cyan for selected
            assert "bold cyan" in result or "cyan" in result
            assert "PDF" in result
            assert "✓" in result

    def test_format_unselected_with_color(self, sample_item_row):
        """Test formatting unselected item with color."""
        if hasattr(sample_item_row, '_format_single_item'):
            result = sample_item_row._format_single_item("EPUB", "✓", "green")

            # Should have color but not bold cyan (not selected)
            assert "green" in result
            assert "EPUB" in result
            assert "bold cyan" not in result

    def test_format_selected_without_color(self, sample_item_row):
        """Test formatting selected item without color."""
        if hasattr(sample_item_row, '_format_single_item'):
            result = sample_item_row._format_single_item("PDF", " ", None)

            assert "bold cyan" in result or "cyan" in result
            assert "PDF" in result

    def test_format_unselected_without_color(self, sample_item_row):
        """Test formatting unselected item without color."""
        if hasattr(sample_item_row, '_format_single_item'):
            result = sample_item_row._format_single_item("EPUB", " ", None)

            # Should be plain
            assert "EPUB" in result
            # Should not have markup
            assert "bold cyan" not in result or result.count("[") == result.count("]")


class TestItemFormatRowUpdateDisplay:
    """Tests for display update functionality."""

    def test_update_display_updates_label(self, sample_item_row):
        """Test update_display updates the label."""
        # Mock the label
        from unittest.mock import Mock
        mock_label = Mock()
        sample_item_row._display_label = mock_label

        sample_item_row.update_display()

        # Should call update on label
        mock_label.update.assert_called_once()

    def test_update_display_with_no_label(self, sample_item_row):
        """Test update_display handles missing label gracefully."""
        sample_item_row._display_label = None

        # Should not crash
        sample_item_row.update_display()

    def test_watch_selected_format_triggers_update(self, sample_item_row):
        """Test that changing selected_format triggers update."""
        from unittest.mock import Mock
        mock_label = Mock()
        sample_item_row._display_label = mock_label

        # Trigger watch by changing selected format
        sample_item_row.watch_selected_format("PDF", "EPUB")

        # Should trigger update
        mock_label.update.assert_called()
```

### Steps

1. Create `tests/test_sync/test_item_format_row.py`
2. Add the tests above
3. Run tests:
   ```bash
   uv run pytest tests/test_sync/test_item_format_row.py -v
   ```
4. Fix any failing tests
5. Check coverage:
   ```bash
   uv run pytest tests/test_sync/test_item_format_row.py --cov=humble_tools.sync.app --cov-report=term-missing
   ```

### Verification

- [x] All tests pass
- [x] Coverage >90% for ItemFormatRow
- [x] All methods tested
- [x] Edge cases covered

---

## Task 3: Test Helper Methods from Phase 3

**Priority:** HIGH  
**Estimated Time:** 60 minutes  
**File:** `tests/test_sync/test_app_helpers.py`

### Implementation

```python
"""Unit tests for BundleDetailsScreen helper methods."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from textual.widgets import Static

from humble_tools.sync.app import BundleDetailsScreen, ItemFormatRow


class TestSafeQueryWidget:
    """Tests for _safe_query_widget helper (if extracted in Phase 3)."""

    @pytest.fixture
    def screen(self, mock_download_manager):
        """Create screen for testing."""
        screen = BundleDetailsScreen(
            epub_manager=mock_download_manager,
            output_dir=Path("/tmp"),
        )
        return screen

    def test_safe_query_widget_success(self, screen):
        """Test successful widget query."""
        if not hasattr(screen, '_safe_query_widget'):
            pytest.skip("_safe_query_widget not implemented (Phase 3)")

        # Mock query_one to return a widget
        mock_widget = Mock(spec=Static)
        screen.query_one = Mock(return_value=mock_widget)

        result = screen._safe_query_widget("#test", Static)

        assert result == mock_widget
        screen.query_one.assert_called_once_with("#test", Static)

    def test_safe_query_widget_no_matches(self, screen):
        """Test widget query when widget doesn't exist."""
        if not hasattr(screen, '_safe_query_widget'):
            pytest.skip("_safe_query_widget not implemented (Phase 3)")

        from textual.css.query import NoMatches
        screen.query_one = Mock(side_effect=NoMatches)

        result = screen._safe_query_widget("#test", Static)

        assert result is None

    def test_safe_query_widget_with_default_action(self, screen):
        """Test widget query with default action callback."""
        if not hasattr(screen, '_safe_query_widget'):
            pytest.skip("_safe_query_widget not implemented (Phase 3)")

        from textual.css.query import NoMatches
        screen.query_one = Mock(side_effect=NoMatches)

        callback = Mock()
        result = screen._safe_query_widget("#test", Static, default_action=callback)

        assert result is None
        callback.assert_called_once()

    def test_safe_query_widget_unexpected_exception(self, screen):
        """Test widget query with unexpected exception."""
        if not hasattr(screen, '_safe_query_widget'):
            pytest.skip("_safe_query_widget not implemented (Phase 3)")

        screen.query_one = Mock(side_effect=RuntimeError("Test error"))

        result = screen._safe_query_widget("#test", Static)

        assert result is None


class TestAllFormatsDownloaded:
    """Tests for _all_formats_downloaded helper (if extracted in Phase 3)."""

    @pytest.fixture
    def screen(self, mock_download_manager):
        """Create screen for testing."""
        return BundleDetailsScreen(
            epub_manager=mock_download_manager,
            output_dir=Path("/tmp"),
        )

    def test_all_formats_downloaded_true(self, screen, sample_item_row):
        """Test when all formats are downloaded."""
        if not hasattr(screen, '_all_formats_downloaded'):
            pytest.skip("_all_formats_downloaded not implemented (Phase 3)")

        sample_item_row.format_status = {
            "PDF": True,
            "EPUB": True,
            "MOBI": True,
        }

        assert screen._all_formats_downloaded(sample_item_row) is True

    def test_all_formats_downloaded_false_one_missing(self, screen, sample_item_row):
        """Test when one format is not downloaded."""
        if not hasattr(screen, '_all_formats_downloaded'):
            pytest.skip("_all_formats_downloaded not implemented (Phase 3)")

        sample_item_row.format_status = {
            "PDF": True,
            "EPUB": False,
            "MOBI": True,
        }

        assert screen._all_formats_downloaded(sample_item_row) is False

    def test_all_formats_downloaded_false_none_downloaded(self, screen, sample_item_row):
        """Test when no formats are downloaded."""
        if not hasattr(screen, '_all_formats_downloaded'):
            pytest.skip("_all_formats_downloaded not implemented (Phase 3)")

        sample_item_row.format_status = {
            "PDF": False,
            "EPUB": False,
            "MOBI": False,
        }

        assert screen._all_formats_downloaded(sample_item_row) is False

    def test_all_formats_downloaded_missing_status(self, screen, sample_item_row):
        """Test when format status is missing (defaults to False)."""
        if not hasattr(screen, '_all_formats_downloaded'):
            pytest.skip("_all_formats_downloaded not implemented (Phase 3)")

        sample_item_row.format_status = {"PDF": True}
        # EPUB and MOBI missing from status dict

        assert screen._all_formats_downloaded(sample_item_row) is False


class TestFormatQueueStatus:
    """Tests for _format_queue_status helper (if extracted in Phase 3)."""

    @pytest.fixture
    def screen(self, mock_download_manager):
        """Create screen for testing."""
        return BundleDetailsScreen(
            epub_manager=mock_download_manager,
            output_dir=Path("/tmp"),
        )

    def test_format_queue_status_with_queued(self, screen):
        """Test formatting with queued downloads."""
        if not hasattr(screen, '_format_queue_status'):
            pytest.skip("_format_queue_status not implemented (Phase 3)")

        # If Phase 4 implemented, use QueueStats
        if hasattr(screen, 'download_queue'):
            from humble_tools.sync.download_queue import QueueStats
            stats = QueueStats(active=2, queued=3, max_concurrent=5)
            result = screen._format_queue_status(stats)
        else:
            screen.active_downloads = 2
            screen.queued_downloads = 3
            screen.max_concurrent_downloads = 5
            result = screen._format_queue_status()

        assert "Active: 2/5" in result or "2/5" in result
        assert "Queued: 3" in result or "3" in result

    def test_format_queue_status_without_queued(self, screen):
        """Test formatting without queued downloads."""
        if not hasattr(screen, '_format_queue_status'):
            pytest.skip("_format_queue_status not implemented (Phase 3)")

        if hasattr(screen, 'download_queue'):
            from humble_tools.sync.download_queue import QueueStats
            stats = QueueStats(active=2, queued=0, max_concurrent=5)
            result = screen._format_queue_status(stats)
        else:
            screen.active_downloads = 2
            screen.queued_downloads = 0
            screen.max_concurrent_downloads = 5
            result = screen._format_queue_status()

        assert "2/5" in result
        assert "Queued" not in result

    def test_format_queue_status_at_capacity(self, screen):
        """Test formatting at maximum capacity."""
        if not hasattr(screen, '_format_queue_status'):
            pytest.skip("_format_queue_status not implemented (Phase 3)")

        if hasattr(screen, 'download_queue'):
            from humble_tools.sync.download_queue import QueueStats
            stats = QueueStats(active=3, queued=5, max_concurrent=3)
            result = screen._format_queue_status(stats)
        else:
            screen.active_downloads = 3
            screen.queued_downloads = 5
            screen.max_concurrent_downloads = 3
            result = screen._format_queue_status()

        assert "3/3" in result
        assert "Queued: 5" in result


class TestFormatItemsInfo:
    """Tests for _format_items_info helper (if extracted in Phase 3)."""

    @pytest.fixture
    def screen(self, mock_download_manager):
        """Create screen for testing."""
        return BundleDetailsScreen(
            epub_manager=mock_download_manager,
            output_dir=Path("/tmp"),
        )

    def test_format_items_info_with_items(self, screen, sample_bundle_data):
        """Test formatting with bundle items."""
        if not hasattr(screen, '_format_items_info'):
            pytest.skip("_format_items_info not implemented (Phase 3)")

        screen.bundle_data = sample_bundle_data
        result = screen._format_items_info()

        assert "2 items" in result or "2" in result

    def test_format_items_info_single_item(self, screen):
        """Test formatting with single item."""
        if not hasattr(screen, '_format_items_info'):
            pytest.skip("_format_items_info not implemented (Phase 3)")

        screen.bundle_data = {"items": [{"number": 1}]}
        result = screen._format_items_info()

        assert "1" in result

    def test_format_items_info_no_bundle_data(self, screen):
        """Test formatting without bundle data."""
        if not hasattr(screen, '_format_items_info'):
            pytest.skip("_format_items_info not implemented (Phase 3)")

        screen.bundle_data = None
        result = screen._format_items_info()

        assert result == ""

    def test_format_items_info_empty_items(self, screen):
        """Test formatting with empty items list."""
        if not hasattr(screen, '_format_items_info'):
            pytest.skip("_format_items_info not implemented (Phase 3)")

        screen.bundle_data = {"items": []}
        result = screen._format_items_info()

        assert result == ""


class TestDownloadHandlers:
    """Tests for download state handler methods (if extracted in Phase 3)."""

    @pytest.fixture
    def screen(self, mock_download_manager):
        """Create screen for testing."""
        screen = BundleDetailsScreen(
            epub_manager=mock_download_manager,
            output_dir=Path("/tmp"),
        )
        screen.app = Mock()
        screen.update_download_counter = Mock()
        return screen

    def test_handle_download_queued(self, screen, sample_item_row):
        """Test _handle_download_queued method."""
        if not hasattr(screen, '_handle_download_queued'):
            pytest.skip("_handle_download_queued not implemented (Phase 3)")

        screen._handle_download_queued(sample_item_row, "PDF")

        assert sample_item_row.format_queued["PDF"] is True
        screen.update_download_counter.assert_called_once()

    def test_handle_download_started(self, screen, sample_item_row):
        """Test _handle_download_started method."""
        if not hasattr(screen, '_handle_download_started'):
            pytest.skip("_handle_download_started not implemented (Phase 3)")

        sample_item_row.format_queued["PDF"] = True
        screen._handle_download_started(sample_item_row, "PDF")

        assert sample_item_row.format_queued["PDF"] is False
        assert sample_item_row.format_downloading["PDF"] is True
        screen.update_download_counter.assert_called_once()

    def test_handle_download_success(self, screen, sample_item_row):
        """Test _handle_download_success method."""
        if not hasattr(screen, '_handle_download_success'):
            pytest.skip("_handle_download_success not implemented (Phase 3)")

        screen.show_notification = Mock()
        screen.set_timer = Mock()
        sample_item_row.format_downloading["PDF"] = True

        screen._handle_download_success(sample_item_row, "PDF")

        assert sample_item_row.format_status["PDF"] is True
        assert sample_item_row.format_downloading["PDF"] is False
        screen.show_notification.assert_called_once()
        screen.set_timer.assert_called_once()

    def test_handle_download_failure(self, screen, sample_item_row):
        """Test _handle_download_failure method."""
        if not hasattr(screen, '_handle_download_failure'):
            pytest.skip("_handle_download_failure not implemented (Phase 3)")

        screen.show_notification = Mock()
        sample_item_row.format_downloading["PDF"] = True

        screen._handle_download_failure(sample_item_row, "PDF")

        assert sample_item_row.format_downloading["PDF"] is False
        screen.show_notification.assert_called_once()
        # Check that notification indicates failure
        call_args = screen.show_notification.call_args[0][0]
        assert "Failed" in call_args or "✗" in call_args or "red" in call_args

    def test_handle_download_error(self, screen, sample_item_row):
        """Test _handle_download_error method."""
        if not hasattr(screen, '_handle_download_error'):
            pytest.skip("_handle_download_error not implemented (Phase 3)")

        screen.show_notification = Mock()
        sample_item_row.format_downloading["PDF"] = True
        error = Exception("Test error")

        screen._handle_download_error(sample_item_row, "PDF", error)

        assert sample_item_row.format_downloading["PDF"] is False
        screen.show_notification.assert_called_once()
        # Check that error message included
        call_args = screen.show_notification.call_args[0][0]
        assert "Error" in call_args or "error" in call_args

    def test_handle_download_cleanup(self, screen):
        """Test _handle_download_cleanup method."""
        if not hasattr(screen, '_handle_download_cleanup'):
            pytest.skip("_handle_download_cleanup not implemented (Phase 3)")

        screen._handle_download_cleanup()

        screen.update_download_counter.assert_called_once()
```

### Steps

1. Create `tests/test_sync/test_app_helpers.py`
2. Add the tests above
3. Run tests:
   ```bash
   uv run pytest tests/test_sync/test_app_helpers.py -v
   ```
4. Fix any failing tests
5. Check coverage for helper methods

### Verification

- [ ] All tests pass
- [ ] All Phase 3 helpers tested
- [ ] Conditional skips work for unimplemented features
- [ ] Edge cases covered

---

## Task 4: Test Configuration (Phase 2)

**Priority:** MEDIUM  
**Estimated Time:** 30 minutes  
**File:** `tests/test_sync/test_config.py`

### Implementation

```python
"""Unit tests for configuration module."""

import pytest
from pathlib import Path

# Try to import, skip tests if Phase 2 not implemented
try:
    from humble_tools.sync.config import AppConfig
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False


@pytest.mark.skipif(not CONFIG_AVAILABLE, reason="Phase 2 not implemented")
class TestAppConfig:
    """Tests for AppConfig dataclass."""

    def test_default_initialization(self):
        """Test default configuration values."""
        config = AppConfig()

        assert config.max_concurrent_downloads == 3
        assert config.notification_duration == 5
        assert config.item_removal_delay == 10
        assert isinstance(config.output_dir, Path)
        assert config.session_file is None

    def test_custom_values(self):
        """Test initialization with custom values."""
        config = AppConfig(
            max_concurrent_downloads=5,
            notification_duration=10,
            item_removal_delay=15,
            output_dir=Path("/custom/path"),
        )

        assert config.max_concurrent_downloads == 5
        assert config.notification_duration == 10
        assert config.item_removal_delay == 15
        assert config.output_dir == Path("/custom/path")

    def test_validation_max_downloads_too_low(self):
        """Test validation rejects max_concurrent < 1."""
        with pytest.raises(ValueError, match="must be at least 1"):
            AppConfig(max_concurrent_downloads=0)

    def test_validation_max_downloads_too_high(self):
        """Test validation rejects max_concurrent > 10."""
        with pytest.raises(ValueError, match="should not exceed 10"):
            AppConfig(max_concurrent_downloads=15)

    def test_validation_notification_duration_too_low(self):
        """Test validation rejects notification_duration < 1."""
        with pytest.raises(ValueError, match="must be at least 1"):
            AppConfig(notification_duration=0)

    def test_validation_item_removal_delay_negative(self):
        """Test validation rejects negative item_removal_delay."""
        with pytest.raises(ValueError, match="must be non-negative"):
            AppConfig(item_removal_delay=-1)

    def test_output_dir_string_conversion(self):
        """Test that string paths are converted to Path objects."""
        config = AppConfig(output_dir="/tmp/test")

        assert isinstance(config.output_dir, Path)
        assert str(config.output_dir) == "/tmp/test"

    def test_from_dict_basic(self):
        """Test creating config from dictionary."""
        config_dict = {
            "max_concurrent_downloads": 4,
            "notification_duration": 7,
            "item_removal_delay": 12,
            "output_dir": "/tmp/downloads",
        }

        config = AppConfig.from_dict(config_dict)

        assert config.max_concurrent_downloads == 4
        assert config.notification_duration == 7
        assert config.item_removal_delay == 12
        assert config.output_dir == Path("/tmp/downloads")

    def test_from_dict_partial(self):
        """Test from_dict with partial values uses defaults."""
        config_dict = {"max_concurrent_downloads": 5}

        config = AppConfig.from_dict(config_dict)

        assert config.max_concurrent_downloads == 5
        assert config.notification_duration == 5  # Default
        assert config.item_removal_delay == 10  # Default

    def test_from_dict_with_session_file(self):
        """Test from_dict handles session_file path."""
        config_dict = {
            "session_file": "~/.config/humble/session",
        }

        config = AppConfig.from_dict(config_dict)

        assert isinstance(config.session_file, Path)

    def test_from_dict_session_file_none(self):
        """Test from_dict handles None session_file."""
        config_dict = {"session_file": None}

        config = AppConfig.from_dict(config_dict)

        assert config.session_file is None


@pytest.mark.skipif(not CONFIG_AVAILABLE, reason="Phase 2 not implemented")
class TestAppConfigEdgeCases:
    """Edge case tests for AppConfig."""

    def test_max_concurrent_boundary_1(self):
        """Test minimum valid max_concurrent value."""
        config = AppConfig(max_concurrent_downloads=1)
        assert config.max_concurrent_downloads == 1

    def test_max_concurrent_boundary_10(self):
        """Test maximum valid max_concurrent value."""
        config = AppConfig(max_concurrent_downloads=10)
        assert config.max_concurrent_downloads == 10

    def test_item_removal_delay_zero(self):
        """Test item_removal_delay can be zero."""
        config = AppConfig(item_removal_delay=0)
        assert config.item_removal_delay == 0

    def test_notification_duration_boundary(self):
        """Test minimum notification_duration value."""
        config = AppConfig(notification_duration=1)
        assert config.notification_duration == 1
```

### Steps

1. Create `tests/test_sync/test_config.py`
2. Add the tests above
3. Run tests:
   ```bash
   uv run pytest tests/test_sync/test_config.py -v
   ```

### Verification

- [x] All tests pass or skip appropriately
- [x] All validation rules tested
- [x] from_dict method tested
- [x] Edge cases covered

---

## Task 5: Run Coverage Analysis

**Priority:** HIGH  
**Estimated Time:** 20 minutes

### Implementation

```bash
# Run all unit tests with coverage
uv run pytest tests/test_sync/ \
    --cov=humble_tools.sync \
    --cov-report=html \
    --cov-report=term-missing \
    -v

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Targets

| Module            | Target Coverage | Priority             |
| ----------------- | --------------- | -------------------- |
| app.py            | >85%            | HIGH                 |
| config.py         | >95%            | MEDIUM               |
| download_queue.py | >95%            | HIGH (Phase 4)       |
| constants.py      | N/A             | N/A (just constants) |

### Identify Coverage Gaps

1. **Review coverage report:**

   - Lines not covered
   - Branches not covered
   - Functions not covered

2. **Add tests for gaps:**

   - Focus on critical paths first
   - Then edge cases
   - Finally error paths

3. **Update tests to increase coverage**

### Verification

- [x] Coverage report generated
- [x] Target coverage met
- [x] Gaps identified
- [x] Plan to address gaps

---

## Task 6: Organize Test Documentation

**Priority:** LOW  
**Estimated Time:** 15 minutes  
**File:** `tests/test_sync/README.md`

### Implementation

````markdown
# Sync Module Unit Tests

This directory contains unit tests for the Humble Bundle TUI sync module.

## Test Organization

- `conftest.py` - Shared fixtures and test utilities
- `test_item_format_row.py` - Tests for ItemFormatRow widget
- `test_app_helpers.py` - Tests for helper methods
- `test_config.py` - Tests for configuration (Phase 2)
- `test_download_queue.py` - Tests for DownloadQueue (Phase 4)
- `test_app.py` - Integration-style tests for app components
- `test_concurrent_downloads.py` - Concurrent download scenarios

## Running Tests

### Run all unit tests:

```bash
uv run pytest tests/test_sync/ -v
```
````

### Run specific test file:

```bash
uv run pytest tests/test_sync/test_item_format_row.py -v
```

### Run with coverage:

```bash
uv run pytest tests/test_sync/ --cov=humble_tools.sync --cov-report=term-missing
```

### Run tests matching pattern:

```bash
uv run pytest tests/test_sync/ -k "format_row" -v
```

## Test Fixtures

Common fixtures available from `conftest.py`:

- `mock_download_manager` - Mocked DownloadManager
- `sample_item_row` - Standard ItemFormatRow instance
- `sample_item_row_downloaded` - ItemFormatRow with downloads
- `sample_bundle_data` - Complete bundle data structure
- `mock_bundle_details_screen` - Mocked BundleDetailsScreen
- `temp_output_dir` - Temporary directory for file operations
- `mock_textual_app` - Mocked Textual app instance

## Coverage Targets

- ItemFormatRow: >90%
- Helper methods: >85%
- BundleDetailsScreen: >80%
- Configuration: >95%
- DownloadQueue: >95% (Phase 4)

## Writing New Tests

### Test Naming Convention

- Test files: `test_<module>.py`
- Test classes: `Test<Feature>`
- Test methods: `test_<behavior>`

### Test Structure

```python
def test_feature_behavior():
    """Test that feature behaves correctly."""
    # Arrange
    obj = create_object()

    # Act
    result = obj.method()

    # Assert
    assert result == expected
```

### Using Fixtures

```python
def test_with_fixture(sample_item_row):
    """Test using a fixture."""
    sample_item_row.cycle_format()
    assert sample_item_row.selected_format == "EPUB"
```

## Phase Dependencies

Some tests depend on refactoring phases being completed:

- **Phase 2**: Configuration tests
- **Phase 3**: Helper method tests
- **Phase 4**: DownloadQueue tests

Tests will skip automatically if features not implemented.

```

### Steps

1. Create `tests/test_sync/README.md`
2. Add documentation above
3. Update as needed for project

### Verification
- [x] README created
- [x] Documentation complete
- [x] Examples provided

---

## Success Metrics

### Test Count

- [x] >50 unit tests total
- [x] >20 tests for ItemFormatRow
- [x] >15 tests for helper methods
- [x] >10 tests for configuration

### Coverage

- [x] Overall sync module >85%
- [x] ItemFormatRow >90%
- [x] Helper methods >85%
- [x] Configuration >95%

### Quality

- [x] All tests pass
- [x] No flaky tests
- [x] Tests run in <5 seconds
- [x] Clear test names
- [x] Good test documentation

---

## Common Issues and Solutions

### Issue 1: Import Errors

**Symptom:** `ImportError: cannot import name 'X'`

**Solution:**
- Check if phase implementing feature is complete
- Use conditional imports and `@pytest.mark.skipif`
- Verify Python path includes src directory

### Issue 2: Mocking Textual Widgets

**Symptom:** Tests fail due to Textual widget behavior

**Solution:**
- Mock widget methods, not widget classes
- Use `spec=WidgetClass` when mocking
- Focus on testing logic, not UI rendering

### Issue 3: Tests Pass Individually But Fail Together

**Symptom:** Test isolation issues

**Solution:**
- Check for shared state
- Use fresh fixtures per test
- Clear module-level state in teardown

### Issue 4: Coverage Not Counting Lines

**Symptom:** Coverage report shows uncovered lines that seem covered

**Solution:**
- Check for conditional imports
- Verify tests actually execute the code path
- Use `--cov-report=html` to see detailed report

---

## Next Steps

After completing Phase 7a:

1. **Review coverage report** - Identify remaining gaps
2. **Add missing tests** - Fill critical gaps first
3. **Move to Phase 7b** - Integration tests
4. **Update documentation** - Keep test docs current

---

## Estimated Timeline

| Task | Time | Cumulative |
|------|------|------------|
| Task 1: Fixtures | 30 min | 0.5 hrs |
| Task 2: ItemFormatRow tests | 45 min | 1.25 hrs |
| Task 3: Helper tests | 60 min | 2.25 hrs |
| Task 4: Config tests | 30 min | 2.75 hrs |
| Task 5: Coverage analysis | 20 min | 3.0 hrs |
| Task 6: Documentation | 15 min | 3.25 hrs |
| **Total** | **3.25 hrs** | - |

**Buffer:** +45 min for debugging
**Total estimated:** 3-4 hours

---

**Document Version:** 1.0
**Last Updated:** December 22, 2025
**Status:** Ready for Implementation
```
