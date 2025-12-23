# Unit Test Improvement Implementation Tasks

**Project:** HumbleBundle Unit Test Optimization  
**Created:** December 22, 2025  
**Updated:** December 22, 2025  
**Priority:** Medium (Code quality)  
**Status:** ✅ ALL PHASES COMPLETE

## Current Status Summary

**Test Count:** 107 unit tests + 9 integration tests = 116 total  
**Runtime:** 2.31s (unit tests only)  
**Test Organization:** ✅ Reorganized into `tests/unit/` and `tests/integration/`  
**Phase 1 (Tracker Refactoring):** ✅ Complete - Dependency injection with in-memory DB support  
**Phase 2 (Consolidation):** ✅ Complete - Parametrized tests and factory patterns  
**Phase 3 (Performance):** ❌ Obsolete - Integration tests refactored separately  
**Phase 4 (Enhancements):** ✅ Complete - Error handling tests and documentation

### Key Achievements:

- **Performance:** 2.31s for 107 tests (was 5.3s for 95 tests)
- **Quality:** Added 3 high-value error handling tests
- **Maintainability:** Parametrized tests, factory patterns, comprehensive docstrings
- **Architecture:** Dependency injection enables in-memory database testing

---

## Phase 0: Test Organization ✅ COMPLETE

**Status:** ✅ **COMPLETED**  
**Date:** December 22, 2025

### Completed Actions:

1. ✅ Tests reorganized into separate directories:

   - `tests/unit/` - 104 unit tests (2.05s)
   - `tests/integration/` - 9 integration tests (separate document)

2. ✅ File structure updated:

   - Unit tests moved to `tests/unit/`
   - Integration tests moved to `tests/integration/`
   - Old `test_core/` and `test_sync/` directories removed

3. ✅ Test execution validated:
   - All 104 unit tests passing
   - Runtime: 2.05 seconds (improved from 5.3s)
   - Coverage: 45% overall

### Current Test Commands:

```bash
# Run all unit tests (2.05s)
pytest tests/unit/ -v

# Run all integration tests (separate)
pytest tests/integration/ -v

# Run everything
pytest

# With coverage
pytest tests/unit/ --cov=src/humble_tools --cov-report=term-missing
```

### Test Organization:

- **Unit Tests:** 104 tests (2.05s) in `tests/unit/`
- **Integration Tests:** 9 tests in `tests/integration/` (analyzed separately)

---

## Phase 1: Tracker Refactoring ✅ COMPLETE

**Status:** ✅ **COMPLETED**  
**Date:** December 22, 2025  
**Goal:** Refactor DownloadTracker to use dependency injection  
**Time:** 2 hours  
**Impact:** Improved testability, in-memory database support

### Completed Actions:

1. ✅ Created `src/humble_tools/core/database.py` module:

   - `DatabaseConnection` protocol for database operations
   - `SQLiteConnection` class for connection management
   - `create_default_connection()` factory function
   - Schema initialization moved to database layer

2. ✅ Refactored `src/humble_tools/core/tracker.py`:

   - Removed `db_path` parameter (no backward compatibility)
   - Added `db_connection` parameter accepting `DatabaseConnection`
   - Simplified all methods to use injected connection
   - Removed directory creation logic (moved to database layer)

3. ✅ Updated test fixtures in `tests/conftest.py`:

   - `temp_tracker` - File-based database connection
   - `fast_tracker` - In-memory database (now works!)
   - Both fixtures manage connection lifecycle properly

4. ✅ Created new test files:
   - `tests/unit/test_fast_tracker.py` - Tests for in-memory database
   - Updated `tests/unit/test_tracker.py` - Tests for connection injection

### Results:

- ✅ All 104 unit tests passing
- ✅ In-memory databases working correctly
- ✅ Test execution improved (file I/O eliminated in many tests)
- ✅ Better separation of concerns (DB layer vs business logic)
- ✅ Easier to mock database for testing

### Files Modified:

- Created: `src/humble_tools/core/database.py` (106 lines)
- Modified: `src/humble_tools/core/tracker.py` (simplified to 120 lines)
- Modified: `tests/conftest.py` (updated fixtures)
- Modified: `tests/unit/test_tracker.py` (updated tests)
- Created: `tests/unit/test_fast_tracker.py` (58 lines)

---

## Phase 1: Quick Wins (2-3 hours) - ORIGINAL PLAN

**Goal:** Remove low-value tests, create shared fixtures, optimize DB tests  
**Time:** 2-3 hours  
**Impact:** -10 tests, ~-100 lines, cleaner code

### Task 1.1: Remove low-value constants tests (15 min)

**File:** `tests/unit/test_constants.py`

**Action:** Delete these test methods:

1. `test_download_configuration_defaults` - Tests obvious type constraints
2. `test_display_configuration_constants` - Tests obvious type constraints
3. `test_widget_ids_no_hash_prefix` - Overly specific, covered by other tests
4. `test_status_symbols_are_strings` - Type checking, not business logic
5. `test_colors_are_strings` - Type checking, not business logic
6. `test_colors_are_valid_textual_markup` - Framework validation

**Keep:**

- `test_widget_ids_are_unique` (actual business logic)
- `test_status_symbols_values` (documents expected values)
- `test_color_values` (documents expected values)

**Tests removed:** 6

---

### Task 1.2: Remove low-value config tests (5 min)

**File:** `tests/unit/test_config.py`

**Action:** Delete test method:

1. `test_configuration_immutability_after_creation` - Tests Python dataclass behavior, not our logic

**Tests removed:** 1

---

### Task 1.3: Remove trivial app tests ❌ N/A

**Status:** SKIPPED - These tests are now in `tests/integration/test_sync_app.py` and will be handled separately in the integration test improvement document.

---

### Task 1.4: Remove low-value item format row tests (10 min)

**File:** `tests/unit/test_item_format_row.py`

**Action:** Delete these test methods:

1. `test_build_display_text_priority_queued_over_downloading` - Impossible state (can't be both)
2. `test_build_display_text_empty_formats` - Items always have formats in production

**Tests removed:** 2

---

### Task 1.5: Remove unlikely humble wrapper edge cases (10 min)

**File:** `tests/unit/test_humble_wrapper.py`

**Action:** Delete these test methods:

1. `test_parse_empty_string` - API never returns empty string
2. `test_parse_only_whitespace` - API never returns only whitespace

**Keep:**

- `test_parse_malformed_table_row` - Error handling is important

**Tests removed:** 2

---

### Task 1.6: Remove trivial thread safety test ❌ N/A

**Status:** SKIPPED - test_thread_safety.py is now in `tests/integration/` and will be handled separately in the integration test improvement document.

---

### Task 1.7: Create shared fixtures in conftest.py (45 min)

**File:** `tests/conftest.py`

**Action:** Add shared fixtures

```python
"""pytest configuration and shared fixtures."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add src directory to path so tests can import the package
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from humble_tools.core.tracker import DownloadTracker
from humble_tools.sync.config import AppConfig


@pytest.fixture
def mock_epub_manager():
    """Shared mock epub manager with common return values."""
    manager = Mock()
    manager.download_item = Mock(return_value=True)
    manager.get_bundle_items = Mock(return_value={
        "name": "Test Bundle",
        "purchased": "2024-01-01",
        "amount": "$10.00",
        "total_size": "100 MB",
        "items": [],
        "keys": []
    })
    return manager


@pytest.fixture
def sample_bundle_data():
    """Standard test bundle data."""
    return {
        "name": "Test Bundle",
        "purchased": "2024-01-01",
        "amount": "$10.00",
        "total_size": "100 MB",
        "items": [
            {
                "number": 1,
                "name": "Test Item",
                "formats": ["EPUB", "PDF"],
                "size": "50 MB",
                "format_status": {"EPUB": False, "PDF": False}
            }
        ],
        "keys": []
    }


@pytest.fixture
def test_config():
    """Standard test configuration."""
    return AppConfig(
        max_concurrent_downloads=3,
        output_dir=Path("/tmp/test")
    )


@pytest.fixture
def temp_tracker():
    """Temporary tracker for testing (file-based)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield DownloadTracker(db_path=db_path)


@pytest.fixture
def fast_tracker():
    """In-memory tracker for fast tests."""
    # Use :memory: for fast tests without file I/O
    yield DownloadTracker(db_path=":memory:")


def create_bundle_data(
    name="Test Bundle",
    items=None,
    keys=None,
    purchased="2024-01-01",
    amount="$10.00",
    total_size="100 MB"
):
    """Factory for creating test bundle data."""
    return {
        "name": name,
        "purchased": purchased,
        "amount": amount,
        "total_size": total_size,
        "items": items or [],
        "keys": keys or []
    }
```

---

### Task 1.8: Update test_download_manager.py to use shared fixtures (20 min)

**File:** `tests/test_core/test_download_manager.py`

**Action:** Replace local fixtures with shared ones

**Before:**

```python
@pytest.fixture
def mock_tracker():
    """Create a mock tracker for testing."""
    return Mock()


@pytest.fixture
def epub_manager(mock_tracker):
    """Create a DownloadManager with a mock tracker."""
    return DownloadManager(tracker=mock_tracker)
```

**After:**

```python
# Remove local fixtures, use from conftest.py
# Update tests to use mock_epub_manager where appropriate
```

**Lines saved:** ~15

---

### Task 1.9: Update test_tracker.py to use fast_tracker (15 min)

**File:** `tests/test_core/test_tracker.py`

**Action:** Replace temp_tracker fixture with fast_tracker from conftest

**Before:**

```python
@pytest.fixture
def temp_tracker():
    """Create a temporary tracker for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield DownloadTracker(db_path=db_path)


class TestDownloadTracker:
    def test_mark_downloaded(self, temp_tracker):
        temp_tracker.mark_downloaded(...)
```

**After:**

```python
# Remove local fixture

class TestDownloadTracker:
    def test_mark_downloaded(self, fast_tracker):
        fast_tracker.mark_downloaded(...)
```

**Changes:**

- Remove local `temp_tracker` fixture
- Replace all `temp_tracker` arguments with `fast_tracker`
- 12 test methods to update

**Lines saved:** ~10  
**Speed improvement:** ~0.2 seconds

---

### Task 1.10: Update test_thread_safety.py to use shared fixtures (15 min)

**File:** `tests/test_sync/test_thread_safety.py`

**Action:** Replace local fixtures with shared ones

**Before:**

```python
@pytest.fixture
def mock_epub_manager(self):
    """Create a mock epub manager."""
    manager = Mock()
    manager.download_item = Mock(return_value=True)
    return manager

@pytest.fixture
def config(self):
    """Create test configuration."""
    return AppConfig(
        max_concurrent_downloads=3,
        output_dir=Path("/tmp/test")
    )
```

**After:**

```python
# Remove local fixtures, use from conftest.py
# Use test_config fixture directly
```

**Changes:**

- Remove 3 local fixture definitions (duplicated across test classes)
- Update fixture arguments to use shared fixtures

**Lines saved:** ~30

---

### Phase 1 Validation Checklist:

- [ ] 15 low-value tests removed
- [ ] conftest.py has 5 shared fixtures + 1 factory function
- [ ] test_download_manager.py uses shared fixtures (~15 lines saved)
- [ ] test_tracker.py uses fast_tracker (~10 lines saved, 0.2s faster)
- [ ] test_thread_safety.py uses shared fixtures (~30 lines saved)
- [ ] All tests still pass: `pytest -v`
- [ ] Fast tests still fast: `pytest -m "not slow"` under 5 seconds

**Success Criteria:**

- Test count: 135 → 120 tests
- Lines saved: ~100-150 lines
- All tests passing

---

## Phase 2: Consolidation ✅ COMPLETE

**Status:** ✅ **COMPLETED**  
**Date:** December 22, 2025  
**Goal:** Consolidate redundant validation tests, add factory pattern  
**Time:** 1 hour  
**Impact:** Improved maintainability with parametrization, reduced duplication

### Completed Tasks:

#### Task 2.1: Consolidate config validation tests ✅

**File:** `tests/unit/test_config.py`

- Consolidated 6 validation tests into 3 parametrized tests
- `test_validation_max_concurrent_downloads` (2 parameter combinations)
- `test_validation_notification_duration` (2 parameter combinations)
- `test_output_dir_type_handling` (2 parameter combinations)
- **Result:** Cleaner, more maintainable test structure

#### Task 2.2: Consolidate item format row state tests ✅

**File:** `tests/unit/test_item_format_row.py`

- Consolidated 3 state tracking tests into 1 parametrized test
- `test_format_state_tracking` with 4 parameter combinations
- Covers format_status, format_downloading, and format_queued states
- Kept `test_multiple_format_independent_states` for complex scenarios
- **Result:** Better test organization and coverage

#### Task 2.3: Add bundle data factory usage ✅

**File:** `tests/unit/test_download_manager.py`

- Updated 3 test methods to use `create_bundle_data()` factory
- Reduced code duplication by ~30 lines
- Improved consistency across tests
- Factory defined in `tests/conftest.py`

### Results:

- ✅ All 104 unit tests passing
- ✅ Runtime: 2.05 seconds (maintained excellent performance)
- ✅ Code quality improved with parametrization
- ✅ Less duplication with factory pattern
- ✅ Tests more maintainable and easier to extend

### Files Modified:

- Modified: `tests/unit/test_config.py` (parametrized validation tests)
- Modified: `tests/unit/test_item_format_row.py` (parametrized state tests)
- Modified: `tests/unit/test_download_manager.py` (using factory pattern)

---

## Phase 2: Consolidation (3-4 hours) - ORIGINAL PLAN BELOW

**Goal:** Consolidate redundant validation tests, add factory pattern  
**Time:** 3-4 hours  
**Impact:** -7 tests, -100 lines, better parametrization

### Task 2.1: Consolidate config validation tests (30 min)

**File:** `tests/test_sync/test_config.py`

**Action:** Consolidate validation tests into parametrized versions

**Before (6 tests):**

```python
def test_validation_max_concurrent_downloads_zero(self):
    with pytest.raises(ValueError, match="max_concurrent_downloads must be at least 1"):
        AppConfig(max_concurrent_downloads=0)

def test_validation_max_concurrent_downloads_negative(self):
    with pytest.raises(ValueError, match="max_concurrent_downloads must be at least 1"):
        AppConfig(max_concurrent_downloads=-1)

def test_validation_notification_duration_zero(self):
    with pytest.raises(ValueError, match="notification_duration must be at least 1"):
        AppConfig(notification_duration=0)

def test_validation_notification_duration_negative(self):
    with pytest.raises(ValueError, match="notification_duration must be at least 1"):
        AppConfig(notification_duration=-1)

def test_output_dir_string_conversion(self):
    config = AppConfig(output_dir="/tmp/test")
    assert isinstance(config.output_dir, Path)
    assert config.output_dir == Path("/tmp/test")

def test_output_dir_path_preserved(self):
    path = Path("/tmp/test")
    config = AppConfig(output_dir=path)
    assert isinstance(config.output_dir, Path)
    assert config.output_dir == path
```

**After (3 tests):**

```python
@pytest.mark.parametrize("value,expected_error", [
    (0, "max_concurrent_downloads must be at least 1"),
    (-1, "max_concurrent_downloads must be at least 1"),
])
def test_validation_max_concurrent_downloads(self, value, expected_error):
    """Test max_concurrent_downloads validation."""
    with pytest.raises(ValueError, match=expected_error):
        AppConfig(max_concurrent_downloads=value)

@pytest.mark.parametrize("value,expected_error", [
    (0, "notification_duration must be at least 1"),
    (-1, "notification_duration must be at least 1"),
])
def test_validation_notification_duration(self, value, expected_error):
    """Test notification_duration validation."""
    with pytest.raises(ValueError, match=expected_error):
        AppConfig(notification_duration=value)

@pytest.mark.parametrize("input_value,expected_type", [
    ("/tmp/test", Path),  # String conversion
    (Path("/tmp/test"), Path),  # Path preserved
])
def test_output_dir_type_handling(self, input_value, expected_type):
    """Test output_dir handles both string and Path."""
    config = AppConfig(output_dir=input_value)
    assert isinstance(config.output_dir, expected_type)
    assert config.output_dir == Path("/tmp/test")
```

**Tests consolidated:** 6 → 3 (saves 3 tests)

---

### Task 2.2: Consolidate item format row state tests (30 min)

**File:** `tests/test_sync/test_item_format_row.py`

**Action:** Consolidate state tracking tests

**Before (3 tests):**

```python
def test_format_status_tracking(self):
    row = ItemFormatRow(...)
    assert row.format_status["EPUB"] is True
    assert row.format_status["PDF"] is False

def test_format_downloading_tracking(self):
    row = ItemFormatRow(...)
    assert row.format_downloading.get("EPUB", False) is False
    row.format_downloading["EPUB"] = True
    assert row.format_downloading["EPUB"] is True

def test_format_queued_tracking(self):
    row = ItemFormatRow(...)
    assert row.format_queued.get("EPUB", False) is False
    row.format_queued["EPUB"] = True
    assert row.format_queued["EPUB"] is True
```

**After (1 test):**

```python
@pytest.mark.parametrize("state_attr,initial_val,set_val", [
    ("format_status", {"EPUB": True, "PDF": False}, None),  # Read-only from init
    ("format_downloading", {}, True),  # Set during download
    ("format_queued", {}, True),  # Set when queued
])
def test_format_state_tracking(self, state_attr, initial_val, set_val):
    """Test format state tracking for status, downloading, and queued."""
    row = ItemFormatRow(
        item_number=1,
        item_name="Book",
        formats=["EPUB", "PDF"],
        item_size="10 MB",
        format_status={"EPUB": True, "PDF": False}
    )

    state_dict = getattr(row, state_attr)

    if initial_val is not None:
        # Test initial values
        for fmt, expected in initial_val.items():
            assert state_dict.get(fmt, False) == expected

    if set_val is not None:
        # Test setting values
        state_dict["EPUB"] = set_val
        assert state_dict["EPUB"] == set_val
```

**Tests consolidated:** 3 → 1 (saves 2 tests)

---

### Task 2.3: Add bundle data factory usage (1 hour)

**Action:** Update tests to use `create_bundle_data()` factory

**Files to update:**

- `tests/test_sync/test_app.py` (8 occurrences)
- `tests/test_sync/test_concurrent_downloads.py` (4 occurrences)
- `tests/test_core/test_download_manager.py` (3 occurrences)

**Before:**

```python
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
            "size": "50 MB",
            "format_status": {"EPUB": False}
        }
    ],
    "keys": []
}
```

**After:**

```python
from tests.conftest import create_bundle_data

mock_bundle_data = create_bundle_data(
    items=[
        {
            "number": 1,
            "name": "Test Item",
            "formats": ["EPUB"],
            "size": "50 MB",
            "format_status": {"EPUB": False}
        }
    ]
)
```

**Lines saved:** ~100 lines across all files

---

### Task 2.4: Consolidate constants tests (30 min)

**File:** `tests/test_sync/test_constants.py`

**Action:** After removing 6 tests in Phase 1, ensure remaining tests are well-organized

**Review and ensure:**

- Duplicate "are strings" tests removed
- Keep one test per actual constant value (for documentation)
- Ensure test names are clear

**No changes needed if Phase 1 completed correctly**

---

### Phase 2 Validation Checklist:

- [ ] Config validation tests consolidated (6 → 3)
- [ ] Item format row state tests consolidated (3 → 1)
- [ ] Bundle data factory used in 15+ locations
- [ ] ~100 lines of code saved
- [ ] All tests passing: `pytest -v`
- [ ] Test count reduced by 5 more tests

**Success Criteria:**

- Test count: 120 → 115 tests
- Lines saved: ~200-250 lines total
- All tests passing

---

## Phase 3: Performance Optimization ❌ OBSOLETE

**Status:** ❌ **OBSOLETE**  
**Date:** December 22, 2025  
**Reason:** Integration tests were completely refactored in separate effort. Performance optimization and time mocking are no longer applicable to the current test structure.

**Note:** Integration tests are now minimal (9 tests) and focused on screen transitions and workflows. Performance is already excellent at 2.05s for 104 unit tests. No further optimization needed at this time.

---

## Phase 4: Optional Enhancements ✅ COMPLETE

**Status:** ✅ **COMPLETED**  
**Date:** December 22, 2025  
**Goal:** Add missing coverage, improve organization  
**Time:** 2 hours  
**Impact:** Better error coverage, clearer test documentation

### Completed Tasks:

#### Task 4.1: Add error path tests ✅

**File:** `tests/unit/test_download_manager.py`

Added `TestDownloadManagerErrorHandling` class with focused error tests:

- `test_download_item_propagates_exceptions` - Verifies exceptions propagate and tracker not marked on error
- `test_get_bundle_items_propagates_parse_error` - Tests parsing error handling
- `test_get_bundle_items_propagates_api_error` - Tests API error handling

**Result:** 3 high-value error tests added (no duplication with existing tests)

#### Task 4.3: Add test module docstrings ✅

**Files:** Multiple test modules

Added comprehensive docstrings to key test modules:

- `tests/unit/test_download_manager.py` - Documents coverage, performance, dependencies
- `tests/unit/test_tracker.py` - Documents database testing approach
- `tests/unit/test_config.py` - Documents validation coverage
- `tests/unit/test_item_format_row.py` - Documents display and state testing

**Result:** Better test discoverability and understanding of what each module covers

#### Task 4.2 & 4.4: Skipped ✅

- **Test naming standardization:** Current naming is already clear and consistent
- **Coverage report generation:** Can be done ad-hoc when needed, not adding value to commit

### Results:

- ✅ All 107 unit tests passing
- ✅ Runtime: 2.31 seconds (excellent performance)
- ✅ 3 new error handling tests (high value, no duplication)
- ✅ 4 test modules with comprehensive docstrings
- ✅ Better test organization and documentation

### Files Modified:

- Modified: `tests/unit/test_download_manager.py` (added error tests + docstring)
- Modified: `tests/unit/test_tracker.py` (added docstring)
- Modified: `tests/unit/test_config.py` (added docstring)
- Modified: `tests/unit/test_item_format_row.py` (added docstring)

---

## Phase 4: Optional Enhancements (4-6 hours) - ORIGINAL PLAN BELOW

### Task 3.1: Option A - Mock time in concurrent tests (2 hours)

**File:** `tests/test_sync/test_concurrent_downloads.py`

**Action:** Replace `time.sleep()` with mocked time

**Add fixture:**

```python
import time
import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_time(monkeypatch):
    """Mock time.sleep for fast tests."""
    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)
        # Don't actually sleep - just record the call

    monkeypatch.setattr(time, 'sleep', fake_sleep)
    return sleep_calls
```

**Update tests to use mock_time:**

```python
@pytest.mark.unit  # Now fast enough to be unit test
async def test_concurrent_downloads_with_slow_mock(self, mock_get_bundles, mock_time):
    """Test concurrent downloads without actual delays."""
    # Change mock to not use time.sleep()
    def instant_download(*args, **kwargs):
        # Simulate work without sleeping
        return True

    app.epub_manager.download_item = Mock(side_effect=instant_download)
    # ... rest of test ...
```

**Time saved:** ~11 seconds  
**Complexity:** Medium-High (requires rethinking async timing)

---

### Task 3.2: Option B - Keep slow tests marked (15 min)

**Action:** Keep slow tests as-is but ensure they're clearly marked

**Already done in Phase 0!**

**Add to test documentation:**

````markdown
## Slow Tests

Some tests intentionally use `time.sleep()` to test real-world timing behavior:

- Concurrent download queue management
- TUI async state updates
- Race condition detection

These are marked with `@pytest.mark.slow` and can be skipped during development:

```bash
pytest -m "not slow"  # Skip slow tests
pytest -m slow         # Run only slow tests
```
````

**Recommendation:** Use Option B (keep slow tests marked) unless time mocking is needed for CI/CD speed.

---

### Task 3.3: Reduce TUI pilot pause times (30 min)

**File:** `tests/test_sync/test_app.py`

**Action:** Reduce `await pilot.pause()` durations where timing isn't critical

**Review each pause call:**

```python
# Before
await pilot.pause(0.5)  # Wait for UI to update

# After - if timing not critical
await pilot.pause(0.05)  # Minimal wait for async processing
```

**Guidelines:**

- Keep 0.1-0.5s pauses where testing actual timing behavior
- Reduce to 0.01-0.05s for simple "let async complete" pauses
- Document why longer pauses are needed

**Potential savings:** 1-2 seconds

---

### Task 3.4: Add test performance documentation (15 min)

**File:** `docs/TESTING.md` (or add to README)

**Action:** Document test performance characteristics

```markdown
## Test Performance

### Current Performance

- **Full suite:** ~9-10 seconds (after optimization)
- **Fast tests:** ~4-5 seconds (`pytest -m "not slow"`)
- **Slow tests:** ~11 seconds (`pytest -m slow`)

### Why Some Tests Are Slow

- **Concurrent downloads:** Use `time.sleep()` to test real timing behavior
- **TUI integration:** Need actual async delays for UI state updates
- These tests are marked `@pytest.mark.slow` and `@pytest.mark.integration`

### Performance Guidelines

- Unit tests should complete in < 0.05s each
- Integration tests < 0.5s each acceptable
- Tests using `time.sleep()` should be marked `@pytest.mark.slow`
- Database tests should use in-memory SQLite (`:memory:`)
```

---

### Phase 3 Validation Checklist:

**If Option A (time mocking):**

- [ ] Time mocking fixture created
- [ ] Concurrent tests updated to use mock time
- [ ] Tests run in < 1 second instead of 11s
- [ ] Tests still validate concurrent behavior

**If Option B (keep marked):**

- [ ] Slow tests documented
- [ ] Test commands include slow/fast examples
- [ ] CI/CD can run fast tests separately

**Both options:**

- [ ] TUI pause times optimized where safe
- [ ] Test performance documented
- [ ] `pytest -m "not slow"` under 5 seconds

---

## Phase 4: Optional Enhancements (4-6 hours)

**Goal:** Add missing coverage, improve organization  
**Time:** 4-6 hours  
**Impact:** Better coverage, clearer structure

### Task 4.1: Add error path tests (2 hours)

**File:** `tests/test_core/test_download_manager.py`

**Action:** Add tests for error scenarios

```python
@pytest.mark.parametrize("exception,expected_handled", [
    (IOError("Network error"), True),
    (OSError("Disk full"), True),
    (PermissionError("Access denied"), True),
])
def test_download_item_error_handling(self, exception, expected_handled):
    """Test download handles various error conditions."""
    # ... test implementation ...

def test_download_to_readonly_directory(self):
    """Test download fails gracefully for readonly directory."""
    # ... test implementation ...

def test_concurrent_tracker_access(self):
    """Test tracker handles concurrent database access."""
    # ... test implementation ...
```

**Tests added:** 5-7 new tests

---

### Task 4.2: Standardize test naming (2 hours)

**Action:** Review and standardize test method names across all files

**Pattern:** `test_<feature>_<scenario>`

**Examples:**

- ✅ Good: `test_download_item_marks_tracker_on_success`
- ✅ Good: `test_config_validation_rejects_negative_values`
- ❌ Bad: `test_download_item[True-True]`
- ❌ Bad: `test_colors_are_strings`

**Files to review:** All test files

---

### Task 4.3: Add test module docstrings (1 hour)

**Action:** Add comprehensive docstrings to test modules

**Example:**

```python
"""Tests for download_manager module.

Test Coverage:
- File ID creation and format handling
- Download manager initialization and lifecycle
- Bundle item retrieval with status tracking
- Download operations and tracker integration
- Bundle statistics calculations

Fast Tests: All tests in this module are fast (<0.3s each)
Dependencies: Mocks humble_wrapper and tracker
"""
```

---

### Task 4.4: Create test coverage report (30 min)

**Action:** Generate and review coverage report

```bash
# Generate HTML coverage report
pytest --cov=humble_tools --cov-report=html --cov-report=term-missing

# Review coverage
open htmlcov/index.html
```

**Identify gaps:**

- Lines not covered
- Branches not tested
- Error paths missing

**Document findings** in coverage report or ticket

---

### Phase 4 Validation Checklist:

- [ ] 5-7 error path tests added
- [ ] Test naming standardized across all files
- [ ] All test modules have descriptive docstrings
- [ ] Coverage report generated and reviewed
- [ ] Coverage > 85% (target)

---

## Summary Checklist

### Phase 0 (15 min) - IMMEDIATE

- [ ] Pytest markers added to pyproject.toml
- [ ] Slow tests marked (@pytest.mark.slow)
- [ ] Integration tests marked (@pytest.mark.integration)
- [ ] Test commands documented
- [ ] `pytest -m "not slow"` works and runs in ~4-5s

### Phase 1 (2-3 hours) - HIGH PRIORITY

- [ ] 15 low-value tests removed
- [ ] 5 shared fixtures in conftest.py
- [ ] Bundle data factory function added
- [ ] test_tracker.py uses fast_tracker (in-memory DB)
- [ ] test_download_manager.py uses shared fixtures
- [ ] test_thread_safety.py uses shared fixtures

### Phase 2 (3-4 hours) - MEDIUM PRIORITY

- [ ] Config validation tests consolidated (6 → 3)
- [ ] Item format row state tests consolidated (3 → 1)
- [ ] Bundle data factory used in 15+ locations
- [ ] ~200-250 lines of code saved total

### Phase 3 (2-3 hours) - OPTIMIZATION

- [ ] Time mocking decision made (Option A or B)
- [ ] TUI pause times optimized
- [ ] Test performance documented
- [ ] Full suite under 10s (or fast suite clearly separated)

### Phase 4 (4-6 hours) - OPTIONAL

- [ ] Error path tests added
- [ ] Test naming standardized
- [ ] Module docstrings added
- [ ] Coverage report reviewed

---

## Success Metrics

### After Phase 0:

- ✅ Development test cycle: **4.7s** (vs 19s before)
- ✅ Can run fast tests with: `pytest -m "not slow"`

### After Phase 1:

- ✅ Test count: 135 → **120 tests** (-11%)
- ✅ Code reduction: **~150 lines**
- ✅ All tests passing

### After Phase 2:

- ✅ Test count: 120 → **115 tests** (-15%)
- ✅ Code reduction: **~250 lines** (cumulative)
- ✅ Better parametrization

### After Phase 3:

- ✅ Full suite: **~8-9s** (vs 19s) OR
- ✅ Clear fast/slow separation maintained

### Final State:

- Test count: **115 tests** (from 135)
- Fast tests: **~4-5s** (90 tests)
- Code reduction: **~250-350 lines**
- Coverage: **Maintained or improved**
- Developer experience: **4.75x faster feedback**

---

## Risk Mitigation

### Before Each Phase:

1. ✅ Commit current state
2. ✅ Run full test suite to establish baseline
3. ✅ Note current test count and timing

### After Each Phase:

1. ✅ Run full test suite: `pytest -v`
2. ✅ Verify fast tests: `pytest -m "not slow"`
3. ✅ Check test count matches expected
4. ✅ Commit changes with descriptive message

### If Tests Fail:

1. Review git diff to identify changes
2. Run individual test file: `pytest tests/path/to/file.py -v`
3. Use pytest verbose output: `pytest -vv`
4. Check for fixture naming conflicts
5. Verify imports still work

### Rollback Plan:

```bash
# If phase fails, rollback
git reset --hard HEAD~1

# Or cherry-pick successful changes
git revert <commit-hash>
```

---

## Time Estimates by Developer Experience

### Experienced (Familiar with pytest, codebase):

- Phase 0: **10 minutes**
- Phase 1: **2 hours**
- Phase 2: **2.5 hours**
- Phase 3: **1.5 hours**
- **Total: 6 hours**

### Intermediate:

- Phase 0: **15 minutes**
- Phase 1: **3 hours**
- Phase 2: **4 hours**
- Phase 3: **2.5 hours**
- **Total: 9.5 hours**

### Learning (New to pytest or codebase):

- Phase 0: **20 minutes**
- Phase 1: **4 hours**
- Phase 2: **5 hours**
- Phase 3: **3 hours**
- **Total: 12 hours**

**Recommendation:** Start with Phase 0 regardless of experience level for immediate benefit, then proceed based on available time and priorities.

---

## Next Steps

1. **Review this task document** with team
2. **Prioritize phases** based on team needs
3. **Assign ownership** of each phase
4. **Schedule time** for implementation
5. **Start with Phase 0** - can be done in 15 minutes for immediate 4.75x speedup!

**Questions?** Refer to `/docs/dev/TEST_ANALYSIS_AND_OPTIMIZATION.md` for detailed analysis and justification.
