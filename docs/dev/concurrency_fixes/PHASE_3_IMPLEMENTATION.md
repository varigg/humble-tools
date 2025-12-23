# Phase 3: Bug Fixes Implementation

**Status:** ⏳ TODO  
**Duration:** 7 hours  
**Priority:** CRITICAL  
**Dependencies:** Phase 2 complete (tests written and failing)

---

## Objective

Implement fixes for all 6 critical bugs, verified by the tests created in Phase 2.

**Approach:** One bug at a time, test-driven, with continuous verification.

---

## Task 3.1: Fix CRITICAL-1 - Database Thread Safety 🔴

**Status:** ⏳ TODO  
**Time:** 1 hour  
**Tests:** `test_tracker_concurrency.py`

### Current State

```bash
$ uv run pytest tests/unit/test_tracker_concurrency.py -v
# All tests FAILING with "database is locked" errors
```

### Implementation Steps

#### Step 3.1.1: Add Lock to DownloadTracker

**File:** `src/humble_tools/core/tracker.py`

```python
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from humble_tools.core.database import DatabaseConnection, create_default_connection


class DownloadTracker:
    """Track downloaded files in a database with thread-safe operations."""

    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """Initialize the download tracker.

        Args:
            db_connection: Database connection. If None, creates default connection.
        """
        if db_connection is None:
            db_connection = create_default_connection()

        self._conn = db_connection
        self._lock = threading.Lock()  # NEW: Protect all database operations

    def mark_downloaded(self, ...):
        """Mark a file as downloaded (thread-safe)."""
        with self._lock:  # Wrap entire operation
            self._conn.execute(...)
            self._conn.commit()

    def is_downloaded(self, file_url: str) -> bool:
        """Check if file is downloaded (thread-safe)."""
        with self._lock:  # Wrap entire operation
            cursor = self._conn.execute(...)
            return cursor.fetchone() is not None

    # Apply same pattern to ALL other methods...
```

**Changes Required:**

- [ ] Add `import threading` to imports
- [ ] Add `self._lock = threading.Lock()` in `__init__`
- [ ] Wrap `mark_downloaded` body with `with self._lock:`
- [ ] Wrap `is_downloaded` body with `with self._lock:`
- [ ] Wrap `get_bundle_stats` body with `with self._lock:`
- [ ] Wrap `get_all_stats` body with `with self._lock:`
- [ ] Wrap `get_tracked_bundles` body with `with self._lock:`
- [ ] Wrap `get_downloaded_files` body with `with self._lock:`

#### Step 3.1.2: Add Database Timeout

**File:** `src/humble_tools/core/database.py`

```python
class SQLiteConnection:
    """SQLite database connection wrapper with schema management."""

    def __init__(self, db_path: str | Path = ":memory:"):
        """Initialize SQLite connection with timeout.

        Args:
            db_path: Path to database file or ":memory:" for in-memory DB
        """
        if isinstance(db_path, Path):
            db_path = str(db_path)

        self._conn = sqlite3.connect(
            db_path,
            check_same_thread=False,
            timeout=5.0  # NEW: 5 second timeout
        )
        self._initialize_schema()
```

**Changes Required:**

- [ ] Add `timeout=5.0` parameter to `sqlite3.connect()`

### Verification

```bash
# Run tracker concurrency tests
uv run pytest tests/unit/test_tracker_concurrency.py -v

# Expected: ALL PASS
# test_concurrent_mark_downloaded_same_bundle PASSED
# test_concurrent_read_write_race PASSED
# test_concurrent_is_downloaded_checks PASSED

# Run existing tracker tests (check for regressions)
uv run pytest tests/unit/test_tracker.py -v

# Expected: ALL PASS (no regressions)
```

### Success Criteria

- ✅ All 3 concurrency tests pass
- ✅ All existing tracker tests still pass
- ✅ No "database is locked" errors
- ✅ Performance acceptable (< 10ms overhead per operation)

---

## Task 3.2: Fix CRITICAL-2 - Duplicate Download Prevention 🔴

**Status:** ⏳ TODO  
**Time:** 1.5 hours  
**Tests:** `test_download_deduplication.py`

### Current State

```bash
$ uv run pytest tests/unit/test_download_deduplication.py -v
# test_rapid_double_click_same_format FAILING - duplicate download
# test_queued_format_not_requeued FAILING - duplicate queueing
```

### Implementation Steps

#### Step 3.2.1: Add Pending Downloads Tracking

**File:** `src/humble_tools/sync/app.py`

```python
class BundleDetailsScreen(Container):
    """Screen showing bundle details and items."""

    def __init__(self, download_manager: DownloadManager, config: AppConfig):
        super().__init__()
        self.download_manager = download_manager
        self.config = config
        self.bundle_key = ""
        self.bundle_name = ""
        self.bundle_data = None
        self._queue = DownloadQueue(max_concurrent=self.config.max_concurrent_downloads)

        # NEW: Track pending downloads to prevent duplicates
        self._pending_downloads: set = set()
        self._pending_lock = threading.Lock()
```

**Changes Required:**

- [ ] Add `import threading` if not already present
- [ ] Add `self._pending_downloads: set = set()` in `__init__`
- [ ] Add `self._pending_lock = threading.Lock()` in `__init__`

#### Step 3.2.2: Implement Atomic Check-and-Add

**File:** `src/humble_tools/sync/app.py`

```python
@work(thread=True)
def download_format(self, item_row: ItemFormatRow) -> None:
    """Download the selected format with deduplication."""
    selected_format = item_row.selected_format

    if selected_format is None:
        return

    # Create unique download key
    download_key = (self.bundle_key, item_row.item_number, selected_format)

    # Atomic check-and-add
    with self._pending_lock:
        # Check all conditions atomically
        if download_key in self._pending_downloads:
            return  # Already pending
        if item_row.format_downloading.get(selected_format, False):
            return  # Already downloading
        if item_row.format_queued.get(selected_format, False):
            return  # Already queued
        if item_row.format_status.get(selected_format, False):
            return  # Already downloaded

        # Mark as pending
        self._pending_downloads.add(download_key)

    try:
        # ... rest of download logic ...
    finally:
        # Always remove from pending
        with self._pending_lock:
            self._pending_downloads.discard(download_key)
```

**Changes Required:**

- [ ] Add download_key creation: `(self.bundle_key, item_row.item_number, selected_format)`
- [ ] Move all early-return checks inside `with self._pending_lock:` block
- [ ] Add `self._pending_downloads.add(download_key)` after checks
- [ ] Wrap existing try block content (no changes to logic)
- [ ] Add finally block with `self._pending_downloads.discard(download_key)`

### Verification

```bash
# Run deduplication tests
uv run pytest tests/unit/test_download_deduplication.py -v

# Expected: ALL PASS
# test_rapid_double_click_same_format PASSED (was failing)
# test_concurrent_downloads_different_formats_allowed PASSED
# test_already_downloaded_not_redownloaded PASSED
# test_queued_format_not_requeued PASSED (was failing)

# Run integration tests (check for regressions)
uv run pytest tests/integration/test_integration_downloads.py -v

# Expected: ALL PASS (no regressions)
```

### Success Criteria

- ✅ `test_rapid_double_click_same_format` passes (was failing)
- ✅ `test_queued_format_not_requeued` passes (was failing)
- ✅ No duplicate downloads under any concurrent scenario
- ✅ Different formats can still download concurrently
- ✅ No performance regression

---

## Task 3.3: Fix CRITICAL-3 - Queue State Recovery 🔴

**Status:** ⏳ TODO  
**Time:** 2 hours  
**Tests:** `test_queue_error_recovery.py`

### Current State

```bash
$ uv run pytest tests/unit/test_queue_error_recovery.py -v
# test_no_double_decrement_if_never_started FAILING
# test_acquire_timeout_doesnt_corrupt_state FAILING
# test_multiple_errors_dont_cause_negative_counters FAILING
```

### Implementation Steps

#### Step 3.3.1: Add Safe call_from_thread Wrapper

**File:** `src/humble_tools/sync/app.py`

```python
class BundleDetailsScreen(Container):
    """Screen showing bundle details and items."""

    # ... existing code ...

    def _safe_call_from_thread(self, callback, *args, **kwargs):
        """Safely call function from thread, handling shutdown.

        Args:
            callback: Function to call on main thread
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        try:
            self.app.call_from_thread(callback, *args, **kwargs)
        except RuntimeError as e:
            # Event loop shut down - expected during app exit
            logging.debug(f"UI update skipped (app shutting down): {e}")
        except Exception as e:
            # Unexpected error - log it
            logging.error(f"Unexpected error in call_from_thread: {e}")
```

**Changes Required:**

- [ ] Add `import logging` to imports
- [ ] Add `_safe_call_from_thread` method to BundleDetailsScreen class

#### Step 3.3.2: Improve Error Handling in download_format

**File:** `src/humble_tools/sync/app.py`

```python
@work(thread=True)
def download_format(self, item_row: ItemFormatRow) -> None:
    """Download with robust error handling."""
    selected_format = item_row.selected_format

    if selected_format is None:
        return

    download_key = (self.bundle_key, item_row.item_number, selected_format)

    # Atomic check-and-add
    with self._pending_lock:
        if download_key in self._pending_downloads:
            return
        if item_row.format_downloading.get(selected_format, False):
            return
        if item_row.format_queued.get(selected_format, False):
            return
        if item_row.format_status.get(selected_format, False):
            return
        self._pending_downloads.add(download_key)

    # Track state transitions
    moved_to_active = False
    acquired_slot = False

    try:
        # Mark as queued
        self._safe_call_from_thread(
            self._handle_download_queued,
            item_row,
            selected_format,
        )

        # Acquire with timeout
        acquired_slot = self._queue.acquire(blocking=True, timeout=1.0)

        if not acquired_slot:
            # Timeout - clean up queued counter
            with self._queue._lock:
                self._queue._queued = max(0, self._queue._queued - 1)
            return

        # Move to active
        self._safe_call_from_thread(
            self._handle_download_started,
            item_row,
            selected_format,
        )
        moved_to_active = True  # Track that we transitioned

        # Perform download
        try:
            success = self.download_manager.download_item(...)
        except HumbleCLIError as e:
            raise DownloadError(...) from e
        except (IOError, OSError) as e:
            raise DownloadError(...) from e

        # Handle result
        if success:
            self._safe_call_from_thread(
                self._handle_download_success,
                item_row,
                selected_format,
            )
        else:
            self._safe_call_from_thread(
                self._handle_download_failure,
                item_row,
                selected_format,
            )

    except Exception as e:
        self._safe_call_from_thread(
            self._handle_download_error,
            item_row,
            selected_format,
            e,
        )

    finally:
        # State-aware cleanup
        if moved_to_active:
            # We made it to active state, do full cleanup
            self._safe_call_from_thread(self._handle_download_cleanup)
        elif acquired_slot:
            # We acquired but never started, just decrement queued
            with self._queue._lock:
                self._queue._queued = max(0, self._queue._queued - 1)

        # Always release semaphore if acquired
        if acquired_slot:
            self._queue.release()

        # Always remove from pending
        with self._pending_lock:
            self._pending_downloads.discard(download_key)
```

**Changes Required:**

- [ ] Replace all `self.app.call_from_thread` with `self._safe_call_from_thread`
- [ ] Add `moved_to_active = False` before try block
- [ ] Add `acquired_slot = False` before try block
- [ ] Set `moved_to_active = True` after mark_started
- [ ] Set `acquired_slot = True` after acquire succeeds
- [ ] Replace finally block with state-aware cleanup logic

### Verification

```bash
# Run queue error recovery tests
uv run pytest tests/unit/test_queue_error_recovery.py -v

# Expected: ALL PASS
# test_queue_state_after_exception_in_download PASSED
# test_no_double_decrement_if_never_started PASSED (was failing)
# test_acquire_timeout_doesnt_corrupt_state PASSED (was failing)
# test_multiple_errors_dont_cause_negative_counters PASSED (was failing)

# Run queue tests (check counters never go negative)
uv run pytest tests/unit/test_download_queue.py -v

# Expected: ALL PASS (no regressions)
```

### Success Criteria

- ✅ All queue recovery tests pass
- ✅ Counters never go negative under any error scenario
- ✅ No semaphore leaks
- ✅ Clean error messages (no stack traces for expected errors)

---

## Task 3.4: Fix CRITICAL-4 & 5 - Graceful Shutdown 🔴

**Status:** ⏳ TODO  
**Time:** 3 hours  
**Tests:** `test_shutdown.py`

### Current State

```bash
$ uv run pytest tests/integration/test_shutdown.py -v
# test_shutdown_with_active_downloads FAILING - dangling threads
# test_call_from_thread_during_shutdown FAILING - uncaught exception
```

### Implementation Steps

#### Step 3.4.1: Add Shutdown Event to HumbleBundleTUI

**File:** `src/humble_tools/sync/app.py`

```python
import threading
import time

class HumbleBundleTUI(App):
    """Main TUI application with graceful shutdown."""

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__()
        self.config = config or AppConfig()
        self.tracker = DownloadTracker()
        self.download_manager = DownloadManager(self.tracker)

        # NEW: Shutdown coordination
        self._shutdown_event = threading.Event()

        # Screens
        self.bundle_list_screen = None
        self.bundle_details_screen = None
        self.current_screen = "list"

    def action_quit(self) -> None:
        """Quit with graceful shutdown."""
        # Signal workers to stop
        self._shutdown_event.set()

        # Give workers a moment to notice
        time.sleep(0.1)

        # Exit
        self.exit()
```

**Changes Required:**

- [ ] Add `import threading` and `import time` to imports
- [ ] Add `self._shutdown_event = threading.Event()` in `__init__`
- [ ] Replace `action_quit` method with shutdown-aware version

#### Step 3.4.2: Check Shutdown Flag in download_format

**File:** `src/humble_tools/sync/app.py`

```python
@work(thread=True)
def download_format(self, item_row: ItemFormatRow) -> None:
    """Download with shutdown awareness."""

    # Check shutdown at entry
    if self.app._shutdown_event.is_set():
        return

    selected_format = item_row.selected_format

    if selected_format is None:
        return

    download_key = (self.bundle_key, item_row.item_number, selected_format)

    # Atomic check-and-add
    with self._pending_lock:
        # ... checks ...
        self._pending_downloads.add(download_key)

    moved_to_active = False
    acquired_slot = False

    try:
        # Mark as queued
        self._safe_call_from_thread(
            self._handle_download_queued,
            item_row,
            selected_format,
        )

        # Check shutdown before blocking
        if self.app._shutdown_event.is_set():
            with self._queue._lock:
                self._queue._queued = max(0, self._queue._queued - 1)
            return

        # Acquire with timeout
        acquired_slot = self._queue.acquire(blocking=True, timeout=1.0)

        if not acquired_slot:
            with self._queue._lock:
                self._queue._queued = max(0, self._queue._queued - 1)
            return

        # Check shutdown after acquire
        if self.app._shutdown_event.is_set():
            with self._queue._lock:
                self._queue._queued = max(0, self._queue._queued - 1)
            return

        # Move to active
        self._safe_call_from_thread(
            self._handle_download_started,
            item_row,
            selected_format,
        )
        moved_to_active = True

        # ... rest of download logic ...
```

**Changes Required:**

- [ ] Add shutdown check at start: `if self.app._shutdown_event.is_set(): return`
- [ ] Add shutdown check before acquire
- [ ] Add shutdown check after acquire
- [ ] Ensure cleanup happens in all shutdown paths

### Verification

```bash
# Run shutdown tests
uv run pytest tests/integration/test_shutdown.py -v

# Expected: ALL PASS
# test_shutdown_with_active_downloads PASSED (was failing)
# test_call_from_thread_during_shutdown PASSED (was failing)

# Manual test - start TUI, start downloads, press 'q'
uv run hb-epub tui
# Expected: App exits cleanly within 2 seconds

# Check for dangling threads
# (Run app, start downloads, quit, check process terminates)
```

### Success Criteria

- ✅ All shutdown tests pass
- ✅ No dangling worker threads after exit
- ✅ App exits within 2 seconds of quit command
- ✅ No uncaught exceptions during shutdown
- ✅ Downloads abort cleanly (no corruption)

---

## Phase 3 Completion Checklist

### Code Changes

- [ ] `src/humble_tools/core/tracker.py` - Added threading.Lock
- [ ] `src/humble_tools/core/database.py` - Added timeout
- [ ] `src/humble_tools/sync/app.py` - Added deduplication
- [ ] `src/humble_tools/sync/app.py` - Added error recovery
- [ ] `src/humble_tools/sync/app.py` - Added shutdown handling

### Test Verification

- [ ] All Task 3.1 tests pass (database concurrency)
- [ ] All Task 3.2 tests pass (deduplication)
- [ ] All Task 3.3 tests pass (error recovery)
- [ ] All Task 3.4 tests pass (shutdown)
- [ ] No regressions in existing tests

### Code Quality

- [ ] Ruff linting passes: `uv run ruff check src/`
- [ ] Ruff formatting passes: `uv run ruff format src/`
- [ ] Type hints complete (no new type: ignore needed)
- [ ] Docstrings updated
- [ ] No TODO comments left in production code

---

## Success Criteria

- ✅ All 6 critical bugs fixed
- ✅ All 14 new tests passing
- ✅ All existing tests still passing
- ✅ No regressions introduced
- ✅ Code quality maintained
- ✅ Performance acceptable

---

## Next Steps

Proceed to **[Phase 4: Verification](PHASE_4_VERIFICATION.md)**

Run comprehensive testing and validation.

---

_Phase 3 Status: TODO_
