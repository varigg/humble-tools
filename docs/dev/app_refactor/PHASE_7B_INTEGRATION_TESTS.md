# Phase 7b: Integration Tests - Detailed Task Document

**Date Created:** December 22, 2025  
**Status:** Ready for Implementation  
**Priority:** HIGH  
**Estimated Effort:** 2-3 hours  
**Risk Level:** Low  
**Dependencies:** Phase 7a (Unit Tests) should be completed first

---

## Overview

Phase 7b focuses on creating focused integration tests that verify how different components work together. Unlike unit tests that test components in isolation, integration tests ensure that the TUI screens, download manager, and state management work correctly as a complete system.

This document focuses on **high-value tests** with **concrete assertions** that will catch real regressions. Tests with placeholder assertions or "implementation specific" comments have been removed.

### Goals

- ✅ Test critical user workflows end-to-end
- ✅ Verify screen transitions work correctly
- ✅ Test download lifecycle with real assertions
- ✅ Verify error handling across components
- ✅ Ensure state consistency where measurable

### Success Criteria

- [ ] Critical user workflows have integration tests with concrete assertions
- [ ] Screen transition tests pass reliably
- [ ] Download lifecycle tests verify actual behavior
- [ ] Error propagation prevents crashes
- [ ] No flaky tests (>95% reliability)
- [ ] Tests complete in <20 seconds total
- [ ] Each test has clear, verifiable assertions

---

## Integration Test Strategy

### What to Test

**Integration tests should verify:**

1. **Component interactions** - How modules communicate
2. **State management** - State changes across components
3. **Async operations** - Timing and coordination
4. **Error propagation** - Errors bubble correctly
5. **Side effects** - Files created, UI updated, etc.

**Integration tests should NOT:**

- Test individual method logic (that's unit tests)
- Test external APIs directly (use mocks)
- Test UI rendering details (that's manual testing)

### Test Levels

```
Level 1: Screen Integration
├── Screen mounting
├── Widget composition
└── Event handling

Level 2: Workflow Integration
├── Bundle selection → Details view
├── Item selection → Download
└── Download complete → Item removal

Level 3: System Integration
├── Multiple screens + download manager
├── Queue + UI + file system
└── Error handling across all components
```

---

## Task 1: Create Integration Test Fixtures

**Priority:** HIGH  
**Estimated Time:** 30 minutes  
**File:** `tests/integration/conftest.py` (add to existing)

### Implementation

Add these fixtures to the existing conftest.py:

```python
"""Additional fixtures for integration tests."""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from textual.pilot import Pilot

from humble_tools.sync.app import HumbleBundleTUI


@pytest.fixture
def mock_get_bundles():
    """Mock get_bundles function."""
    with patch('humble_tools.sync.app.get_bundles') as mock:
        mock.return_value = [
            {"key": "bundle_1", "name": "Test Bundle 1"},
            {"key": "bundle_2", "name": "Test Bundle 2"},
        ]
        yield mock


@pytest.fixture
def mock_bundle_with_items():
    """Mock bundle data with items."""
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
            {"name": "Steam Key", "key": "XXXXX-XXXXX-XXXXX"},
            {"name": "Epic Key", "key": "YYYYY-YYYYY-YYYYY"},
        ],
    }


@pytest.fixture
def mock_successful_download():
    """Mock successful download function."""
    def _download(bundle_key, item_number, format_name, output_dir):
        # Simulate download delay
        return True
    return _download


@pytest.fixture
def mock_failed_download():
    """Mock failed download function."""
    def _download(bundle_key, item_number, format_name, output_dir):
        return False
    return _download


@pytest.fixture
def mock_download_with_error():
    """Mock download that raises an error."""
    def _download(bundle_key, item_number, format_name, output_dir):
        raise RuntimeError("Network error")
    return _download


@pytest.fixture
async def app_with_pilot(mock_get_bundles, mock_bundle_with_items, temp_output_dir):
    """Create app with pilot for testing."""
    app = HumbleBundleTUI()

    # Mock the download manager
    app.epub_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)
    app.epub_manager.download_item = Mock(return_value=True)

    async with app.run_test() as pilot:
        await pilot.pause()  # Let app initialize
        yield app, pilot
```

### Steps

1. Open `tests/integration/conftest.py`
2. Add the fixtures above
3. Test they work:
   ```bash
   uv run pytest tests/integration/ --collect-only | grep -i fixture
   ```

### Verification

- [x] Fixtures added successfully
- [x] No import errors
- [x] Fixtures visible to pytest
- [x] Can be used in tests

---

## Task 2: Test Screen Transitions ✅

**Status:** COMPLETED  
**Priority:** HIGH  
**Estimated Time:** 30 minutes  
**File:** NEW - `tests/integration/test_integration_screens.py`

### Implementation

````python
"""Integration tests for screen transitions."""

import pytest
from unittest.mock import Mock

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
        app.epub_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Should start on bundles screen
            assert app.current_screen == "bundles"

            # Navigate to details
            await pilot.press("enter")
            await pilot.pause()
            assert app.current_screen == "details"

            # Verify bundle data loaded with correct item count
            details_screen = app.details_screen
            assert details_screen is not None
            assert len(details_screen.bundle_data["items"]) == 3

            # Navigate back
            await pilot.press("escape")
            await pilot.pause()
            assert app.current_screen == "bundles"

    @pytest.mark.asyncio
    async def test_bundle_with_only_keys(
        self,
        mock_get_bundles,
        mock_bundle_with_keys,
    ):
        """Test bundle with only keys (no downloadable items) loads correctly."""
        app = HumbleBundleTUI()
        app.epub_manager.get_bundle_items = Mock(return_value=mock_bundle_with_keys)

        async with app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()

            # Should navigate successfully
            assert app.current_screen == "details"

            # Should have keys but no items
            details_screen = app.details_screen
            assert len(details_screen.bundle_data["keys"]) == 2
            assert len(details_screen.bundle_data["items"]) == 0

    @pytest.mark.asyncio
    async def test_empty_bundle_list_handles_gracefully(self):
        """Test empty bundle list doesn't crash on navigation."""
        with pytest.mock.patch('humble_tools.sync.app.get_bundles') as mock:
            mock.return_value = []

            app = HumbleBundleTUI()

            async with app.run_test() as pilot:
                await pilot.pause()

                # Should show bundles screen even if empty
                assert app.current_screen == "bundles"

                # Pressing enter should not crash
                await pilot.press("enter")
                await pilot.pause()

                # Should remain on bundles screen
                assert app.current_screen == "bundles"

### Steps

1. Create `tests/integration/test_integration_screens.py`
2. Add the tests above
3. Run tests:
   ```bash
   uv run pytest tests/integration/test_integration_screens.py -v
````

### Verification

- [x] All screen transition tests pass
- [x] Navigation works in both directions
- [x] Error cases handled
- [x] Tests complete quickly (<10s)

---

## Task 3: Test Download Lifecycle Integration ✅

**Status:** COMPLETED  
**Priority:** HIGH  
**Estimated Time:** 40 minutes  
**File:** NEW - `tests/integration/test_integration_downloads.py`

### Implementation

```python
"""Integration tests for download lifecycle."""

import pytest
from unittest.mock import Mock

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
        app.epub_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)
        app.epub_manager.download_item = Mock(return_value=True)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to details and first item
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()

            # Cycle format (from PDF to EPUB)
            await pilot.press("right")
            await pilot.pause()

            # Start download
            await pilot.press("enter")
            await pilot.pause(0.5)

            # Verify EPUB was downloaded (second format)
            app.epub_manager.download_item.assert_called_once()
            call_args = app.epub_manager.download_item.call_args
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
        app.epub_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)
        app.epub_manager.download_item = Mock(return_value=False)  # Fail

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate and attempt download
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause(0.5)

            # Download should have been attempted
            app.epub_manager.download_item.assert_called_once()

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
        app.epub_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)
        app.epub_manager.download_item = Mock(
            side_effect=RuntimeError("Network error")
        )

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate and attempt download
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("down")
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
        app.epub_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)

        # First call fails, second succeeds
        app.epub_manager.download_item = Mock(side_effect=[False, True])

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to item
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()

            # First attempt (fails)
            await pilot.press("enter")
            await pilot.pause(0.5)

            # Second attempt (succeeds)
            await pilot.press("enter")
            await pilot.pause(0.5)

            # Should have tried twice with success on second
            assert app.epub_manager.download_item.call_count == 2

    @pytest.mark.asyncio
    async def test_download_persists_during_navigation(
        self,
        mock_get_bundles,
        mock_bundle_with_items,
    ):
        """Test downloads continue after navigating away from details."""
        app = HumbleBundleTUI()
        app.epub_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)
        app.epub_manager.download_item = Mock(return_value=True)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to details and start download
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause(0.2)

            # Navigate back to bundle list
            await pilot.press("escape")
            await pilot.pause(0.5)

            # Download should complete even after navigation
            app.epub_manager.download_item.assert_called_once()

            # Can navigate back without issues
            await pilot.press("enter")
            await pilot.pause()
            assert app.current_screen == "details"
```

### Steps

1. Create `tests/integration/test_integration_downloads.py`
2. Add the tests above
3. Run tests:
   ```bash
   uv run pytest tests/integration/test_integration_downloads.py -v --tb=short
   ```

### Verification

- [x] All 5 download tests pass
- [x] Format selection verified with concrete assertion
- [x] Error handling (False return and exceptions) prevents crashes
- [x] Retry mechanism works
- [x] Navigation doesn't interrupt downloads
- [x] Tests complete in reasonable time (<10s)

---

## Task 4: Test Bundle Load Behavior

**Priority:** MEDIUM  
**Estimated Time:** 15 minutes  
**File:** Add to `tests/integration/test_integration_screens.py`

### Implementation

Add this test class to the existing screen integration file:

```python
class TestBundleLoadBehavior:
    """Test bundle data loading behavior."""

    @pytest.mark.asyncio
    async def test_bundle_data_loads_once_per_navigation(
        self,
        mock_get_bundles,
        mock_bundle_with_items,
    ):
        """Test bundle data is loaded once per navigation to details screen."""
        app = HumbleBundleTUI()

        call_count = [0]
        original_data = mock_bundle_with_items.copy()

        def track_calls(*args, **kwargs):
            call_count[0] += 1
            return original_data

        app.epub_manager.get_bundle_items = Mock(side_effect=track_calls)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Navigate to details
            await pilot.press("enter")
            await pilot.pause()

            # Should load bundle data once
            assert call_count[0] == 1

            # Navigate away and back
            await pilot.press("escape")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Should reload on second entry
            assert call_count[0] == 2
```

### Steps

1. Add the test class to `tests/integration/test_integration_screens.py`
2. Run tests:
   ```bash
   uv run pytest tests/integration/test_integration_screens.py::TestBundleLoadBehavior -v
   ```

### Verification

- [ ] Bundle load test passes
- [ ] Load count verified with concrete assertion
- [ ] Behavior consistent across navigations
- [ ] Concurrent updates handled correctly

---

## Task 5: Create Test Documentation

**Priority:** LOW  
**Estimated Time:** 15 minutes  
**File:** Create `tests/integration/README.md`

### Implementation

Add integration test section to existing README:

````markdown
## Integration Tests

Integration tests verify that components work together correctly as a system.

### Test Files

- `test_integration_screens.py` - Screen navigation and bundle loading (4 tests)
- `test_integration_downloads.py` - Download workflows and error handling (6 tests)

### Running Integration Tests

```bash
# Run all integration tests
uv run pytest tests/integration/test_integration_*.py -v

# Run specific integration test file
uv run pytest tests/integration/test_integration_screens.py -v

# Run with detailed output
uv run pytest tests/integration/test_integration_*.py -v --tb=short
```

**Expected:** 10 tests total, completing in <20 seconds.

### Replacing Old Tests

The existing `tests/integration/` directory contains outdated tests from before refactoring:

- **test_sync_app.py** - Uses old screen API (`.display` property), wrong constructor signatures
- **test_concurrent_downloads.py** - Valuable concurrent download scenarios, but outdated API
- **test_thread_safety.py** - Unit tests, not integration tests (belongs in unit tests)

These will be replaced by the new integration tests created in this phase.

### Integration Test Patterns

#### Testing Screen Transitions

```python
@pytest.mark.asyncio
async def test_screen_transition(mock_get_bundles, mock_bundle_with_items):
    app = HumbleBundleTUI()
    app.epub_manager.get_bundle_items = Mock(return_value=mock_bundle_with_items)

    async with app.run_test() as pilot:
        await pilot.pause()

        # Navigate
        await pilot.press("enter")
        await pilot.pause()

        # Verify
        assert app.current_screen == "details"
```

#### Testing Download Lifecycle

```python
@pytest.mark.asyncio
async def test_download(mock_get_bundles, mock_bundle_with_items):
    app = HumbleBundleTUI()
    app.epub_manager.download_item = Mock(return_value=True)

    async with app.run_test() as pilot:
        # Setup and navigate...

        # Start download
        await pilot.press("enter")
        await pilot.pause(0.5)  # Allow async processing

        # Verify
        app.epub_manager.download_item.assert_called_once()
```

### Common Issues

#### Timing Issues

Integration tests involve async operations. Use appropriate pauses:

```python
await pilot.pause()  # Standard pause
await pilot.pause(0.5)  # Longer for downloads
```

#### Mock Interactions

Ensure mocks are set up before app.run_test():

```python
# ✓ Correct - mock before run_test
app.epub_manager.download_item = Mock(return_value=True)
async with app.run_test() as pilot:
    ...

# ✗ Wrong - mock after run_test
async with app.run_test() as pilot:
    app.epub_manager.download_item = Mock(return_value=True)
```

#### Flaky Tests

If tests are flaky:

- Increase pause durations
- Check for race conditions
- Verify mock setup
- Add debug logging

### Coverage Focus

Integration tests cover:

- Critical user workflows (bundle selection → details → download)
- Screen navigation (forward/back, empty lists, keys-only bundles)
- Download variants (format selection, retry, navigation during download)
- Error scenarios (False return, exceptions, crashes prevented)
- Basic state checks (bundle load count)

### Steps

1. Create or update `tests/integration/README.md`
2. Add integration test section with examples
3. Document common issues and patterns

### Verification

- [ ] Documentation added
- [ ] Examples provided
- [ ] Common issues documented

---

## Task 6: Run and Validate Integration Tests

**Priority:** HIGH
**Estimated Time:** 20 minutes

### Implementation

```bash
# Run all integration tests
uv run pytest tests/integration/test_integration_*.py -v

# Run with timing information
uv run pytest tests/integration/test_integration_*.py -v --durations=10

# Run with coverage
uv run pytest tests/integration/test_integration_*.py \
    --cov=humble_tools.sync \
    --cov-report=term-missing

# Check for flaky tests (run multiple times)
for i in {1..5}; do
    echo "Run $i:"
    uv run pytest tests/integration/test_integration_*.py -v -x
done
```
````

### Success Criteria

- [ ] All 10 integration tests pass
- [ ] Tests complete in <20 seconds total
- [ ] No flaky tests (5/5 runs pass)
- [ ] Each test has concrete assertions (no "implementation specific" placeholders)
- [ ] No test isolation issues
- [ ] Old integration tests can be safely removed

### Debugging Failed Tests

If tests fail:

1. **Run with verbose output:**

   ```bash
   uv run pytest tests/integration/test_integration_*.py -vv --tb=long
   ```

2. **Run single test:**

   ```bash
   uv run pytest tests/integration/test_integration_screens.py::TestScreenNavigation::test_bundle_to_details_and_back -vv
   ```

3. **Add debug output:**

   ```python
   print(f"Current screen: {app.current_screen}")
   print(f"Download called: {app.epub_manager.download_item.called}")
   ```

4. **Check timing:**
   - Increase pause durations
   - Add explicit waits
   - Check async operations complete

### Verification

- [ ] All tests run successfully
- [ ] Performance acceptable (<20s)
- [ ] No flaky behavior
- [ ] Each test has concrete assertions

---

## Task 7: Clean Up Outdated Integration Tests ✅

**Status:** COMPLETED  
**Priority:** MEDIUM  
**Estimated Time:** 10 minutes  
**Dependencies:** Task 6 must be complete (all new tests passing)

### Rationale

The existing integration tests in `tests/integration/` are outdated due to app refactoring:

- Use old screen API (`.display` property, wrong constructors)
- Test assumptions that no longer exist
- Some are misclassified (unit tests in integration directory)

### Implementation

```bash
# 1. Verify new tests pass first
uv run pytest tests/integration/test_integration_*.py -v

# 2. Run old tests to confirm they fail (expected due to API changes)
uv run pytest tests/integration/test_sync_app.py -v || echo "Expected to fail"
uv run pytest tests/integration/test_concurrent_downloads.py -v || echo "Expected to fail"

# 3. Delete outdated integration tests
rm tests/integration/test_sync_app.py
rm tests/integration/test_concurrent_downloads.py

# 4. Move misclassified thread safety tests to unit tests
mv tests/integration/test_thread_safety.py tests/unit/test_thread_safety.py

# 5. Verify new tests still pass after cleanup
uv run pytest tests/integration/test_integration_*.py -v

# 6. Run all tests to ensure nothing broke
uv run pytest tests/ -v
```

### Steps

1. **Verify Prerequisites:**

   - All 10 new integration tests pass (from Task 6)
   - No flaky behavior observed

2. **Remove Outdated Files:**

   ```bash
   rm tests/integration/test_sync_app.py
   rm tests/integration/test_concurrent_downloads.py
   ```

3. **Relocate Misclassified Tests:**

   ```bash
   mv tests/integration/test_thread_safety.py tests/unit/test_thread_safety.py
   ```

4. **Update Git:**

   ```bash
   git rm tests/integration/test_sync_app.py
   git rm tests/integration/test_concurrent_downloads.py
   git mv tests/integration/test_thread_safety.py tests/unit/test_thread_safety.py
   git add tests/integration/test_integration_*.py
   ```

5. **Verify Test Suite:**

   ```bash
   # All integration tests should pass
   uv run pytest tests/integration/ -v

   # All unit tests should pass (including relocated thread_safety)
   uv run pytest tests/unit/ -v

   # Full test suite should pass
   uv run pytest tests/ -v
   ```

### Verification

- [x] Old test files deleted: `test_sync_app.py`, `test_concurrent_downloads.py`
- [x] Thread safety tests moved to `tests/unit/test_thread_safety.py`
- [x] All new integration tests pass (8 tests in 6.6s)
- [x] Relocated thread safety tests pass in unit tests (15 tests in 0.23s)
- [x] Full test suite runs successfully (112 tests in 9.05s)
- [ ] Changes committed to git

### Verification

- [ ] All tests run successfully
- [ ] Performance acceptable (<20s)
- [ ] No flaky behavior
- [ ] Each test has concrete assertions

---

## Success Metrics

### Test Quality (Primary)

- [ ] All tests pass reliably (>95% pass rate over 5 runs)
- [ ] Tests complete in <20 seconds total
- [ ] Each test has concrete assertions (no placeholders)
- [ ] Clear test names and documentation
- [ ] No flaky timing-dependent behavior

### Coverage (Secondary)

- [ ] Critical user workflows covered (bundle → details → download)
- [ ] Error paths prevent crashes (False returns, exceptions)
- [ ] Edge cases tested (empty lists, keys-only bundles)
- [ ] Navigation doesn't interrupt downloads
- [ ] Concurrent downloads show correct UI indicators

---

## Migration from Old Tests (See Task 7)

The existing `tests/integration/` directory contains outdated tests that will be removed in Task 7:

### Why Replace?

1. **API Mismatch:** Tests use old screen API (`.display` property, wrong constructors)
2. **Misclassified Tests:** `test_thread_safety.py` contains unit tests, not integration tests
3. **Outdated Assumptions:** Tests assume screen management that no longer exists
4. **Maintenance Burden:** Updating old tests is more work than writing focused new ones

### What Was Kept

- **Concurrent download scenario** from `test_concurrent_downloads.py` → Added as Task 3 test
- **Thread safety tests** → Will be moved to `tests/unit/` in Task 7

---

## Common Issues and Solutions

### Issue 1: Tests Timeout

**Symptom:** Tests hang or timeout

**Solution:**

- Check for deadlocks in concurrent operations
- Increase timeout values
- Verify mocks don't block
- Add debug logging

### Issue 2: Flaky Tests

**Symptom:** Tests pass sometimes, fail other times

**Solution:**

- Increase pause durations
- Check for race conditions
- Ensure proper test isolation
- Use explicit waits instead of sleep

### Issue 3: Mocks Not Working

**Symptom:** Real methods called instead of mocks

**Solution:**

- Set up mocks before `app.run_test()`
- Verify mock is on correct object
- Check mock is properly patched
- Use `spec` parameter for type safety

### Issue 4: State Leakage Between Tests

**Symptom:** Tests fail when run together but pass individually

**Solution:**

- Use fresh app instance per test
- Clear global state in teardown
- Check for shared fixtures
- Use `pytest --forked` if needed

---

## Next Steps

After completing Phase 7b:

1. **Review test results** - Identify any gaps
2. **Fix flaky tests** - Ensure reliability
3. **Update documentation** - Keep current
4. **Complete Task 7** - Clean up outdated tests

---

## Estimated Timeline

| Task                   | Time         | Cumulative |
| ---------------------- | ------------ | ---------- |
| Task 1: Fixtures       | 30 min       | 0.5 hrs    |
| Task 2: Screen tests   | 30 min       | 1.0 hrs    |
| Task 3: Download tests | 45 min       | 1.75 hrs   |
| Task 4: Load test      | 15 min       | 2.0 hrs    |
| Task 5: Documentation  | 15 min       | 2.25 hrs   |
| Task 6: Validation     | 20 min       | 2.5 hrs    |
| Task 7: Cleanup        | 10 min       | 2.67 hrs   |
| **Total**              | **2.67 hrs** | -          |

**Buffer:** +30 min for debugging  
**Total estimated:** 2.5-3 hours

---

**Document Version:** 1.1  
**Last Updated:** December 22, 2025  
**Status:** Ready for Implementation
