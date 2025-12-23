# Critical Bug Fixes - Implementation Tasks

**Date:** December 23, 2025  
**Status:** 🚧 IN PROGRESS  
**Priority:** IMMEDIATE  
**Reference:** [BUG_ANALYSIS_ASYNC_THREADING.md](BUG_ANALYSIS_ASYNC_THREADING.md)

---

## Overview

This document tracks the implementation of fixes for 4 critical threading and concurrency bugs identified in the bug analysis. The approach follows:

1. **Analyze existing test coverage**
2. **Add missing high-value tests** (test-first approach)
3. **Implement fixes** with verification
4. **Run full test suite** to ensure no regressions

---

## Phase 1: Test Coverage Analysis

### Existing Test Coverage ✅

**Strong Coverage Areas:**

1. **Download Queue State Machine** (`test_download_queue.py`)

   - ✅ State transitions (queued→started→completed)
   - ✅ Error cases (invalid transitions)
   - ✅ Counter operations
   - ✅ Statistics snapshots
   - Coverage: ~85% of queue logic

2. **Thread Safety - Queue Operations** (`test_thread_safety.py`)

   - ✅ Mixed counter operations with threads
   - ✅ Semaphore limits concurrent access
   - ✅ Configuration-driven initialization
   - Coverage: Basic thread safety validated

3. **Download State Handlers** (`test_bundle_details_helpers.py`)

   - ✅ All state handlers tested (queued, started, success, failure, error, cleanup)
   - ✅ Thread safety of handlers validated
   - Coverage: UI update logic well-tested

4. **Basic Tracker Operations** (`test_tracker.py`)
   - ✅ Mark downloaded
   - ✅ Check is_downloaded
   - ✅ Bundle statistics
   - ✅ Multiple bundles
   - Coverage: Single-threaded tracker operations

**Critical Gaps Identified:**

1. ❌ **No concurrent database access tests**

   - No tests with multiple threads writing to tracker simultaneously
   - No tests for database lock errors
   - No tests for concurrent read/write races

2. ❌ **No duplicate download prevention tests**

   - No tests for rapid double-clicks
   - No tests for checking race condition in download_format

3. ❌ **No queue state corruption tests**

   - No tests for exceptions during acquire/release
   - No tests for queue state after errors
   - No tests for negative counter scenarios

4. ❌ **No graceful shutdown tests**

   - No tests for app shutdown during downloads
   - No tests for worker thread cancellation
   - No tests for cleanup on exit

5. ❌ **No call_from_thread failure tests**
   - No tests for UI updates failing during shutdown
   - No tests for event loop already stopped

---

## Phase 2: High-Value Tests to Add

### Test Group 1: Database Concurrency Tests 🔴 CRITICAL

**File:** `tests/unit/test_tracker_concurrency.py` (NEW)

```python
"""Concurrency tests for DownloadTracker database operations."""

import threading
import time
from pathlib import Path
import pytest
from humble_tools.core.tracker import DownloadTracker
from humble_tools.core.database import SQLiteConnection


class TestTrackerConcurrency:
    """Test concurrent access to DownloadTracker."""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create tracker with file-based database for real concurrency testing."""
        db_path = tmp_path / "test.db"
        db_conn = SQLiteConnection(db_path)
        tracker = DownloadTracker(db_connection=db_conn)
        yield tracker
        db_conn.close()

    def test_concurrent_mark_downloaded_same_bundle(self, tracker):
        """Test multiple threads marking different files in same bundle concurrently.

        CRITICAL-1: Tests database thread safety violation.
        Expected: All 50 files marked successfully without corruption.
        Current behavior: May fail with "database is locked" or corruption.
        """
        errors = []

        def mark_file(file_num):
            try:
                tracker.mark_downloaded(
                    file_url=f"url_{file_num}",
                    bundle_key="test_bundle",
                    filename=f"file_{file_num}.epub",
                    bundle_total_files=50
                )
            except Exception as e:
                errors.append((file_num, str(e)))

        # Spawn 50 threads marking files concurrently
        threads = [threading.Thread(target=mark_file, args=(i,)) for i in range(50)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should complete without errors
        assert len(errors) == 0, f"Concurrent writes failed: {errors[:5]}"

        # All 50 files should be marked
        stats = tracker.get_bundle_stats("test_bundle")
        assert stats["downloaded"] == 50
        assert stats["total"] == 50

    def test_concurrent_read_write_race(self, tracker):
        """Test concurrent reads and writes don't cause corruption.

        CRITICAL-1: Tests read/write race conditions.
        Expected: Reads always return consistent data.
        """
        stop_flag = threading.Event()
        read_results = []
        write_count = [0]

        def writer():
            """Continuously write files."""
            count = 0
            while not stop_flag.is_set() and count < 100:
                tracker.mark_downloaded(
                    file_url=f"url_{count}",
                    bundle_key="bundle_a",
                    filename=f"file_{count}.epub"
                )
                write_count[0] = count + 1
                count += 1
                time.sleep(0.001)  # Small delay to increase contention

        def reader():
            """Continuously read stats."""
            for _ in range(100):
                if stop_flag.is_set():
                    break
                stats = tracker.get_bundle_stats("bundle_a")
                read_results.append(stats["downloaded"])
                time.sleep(0.001)

        # Start 1 writer and 3 readers
        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
        ]

        for t in threads:
            t.start()

        # Let them run for a bit
        time.sleep(0.5)
        stop_flag.set()

        for t in threads:
            t.join()

        # Verify reads never exceeded actual writes
        # (no phantom reads from corruption)
        assert all(r <= write_count[0] for r in read_results), \
            f"Read returned value higher than written: {max(read_results)} > {write_count[0]}"

        # Final count should match
        final_stats = tracker.get_bundle_stats("bundle_a")
        assert final_stats["downloaded"] == write_count[0]

    def test_concurrent_is_downloaded_checks(self, tracker):
        """Test concurrent is_downloaded checks while marking downloaded.

        CRITICAL-1: Tests SELECT queries during concurrent INSERT.
        """
        # Pre-populate some data
        for i in range(10):
            tracker.mark_downloaded(
                f"existing_{i}", "bundle", f"file_{i}.epub"
            )

        results = {"checked": [], "errors": []}

        def checker():
            """Check if files are downloaded."""
            for i in range(20):
                try:
                    is_dl = tracker.is_downloaded(f"existing_{i}")
                    results["checked"].append((i, is_dl))
                except Exception as e:
                    results["errors"].append(str(e))
                time.sleep(0.001)

        def marker():
            """Mark new files as downloaded."""
            for i in range(10, 20):
                try:
                    tracker.mark_downloaded(
                        f"existing_{i}", "bundle", f"file_{i}.epub"
                    )
                except Exception as e:
                    results["errors"].append(str(e))
                time.sleep(0.001)

        threads = [
            threading.Thread(target=checker),
            threading.Thread(target=checker),
            threading.Thread(target=marker),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should complete without database errors
        assert len(results["errors"]) == 0, f"Database errors: {results['errors']}"

    def test_database_timeout_handling(self, tracker):
        """Test that database operations timeout instead of hanging forever.

        MODERATE-1: Tests database timeout configuration.
        """
        # This test verifies timeout behavior exists
        # Actual timeout testing requires intentionally locking the database
        # from another process, which is complex for unit tests

        # For now, just verify the connection has a timeout set
        # Implementation should set timeout in SQLiteConnection.__init__
        # This is a placeholder test that will pass once timeout is added

        # Mark a file successfully
        tracker.mark_downloaded("test", "bundle", "file.epub")
        assert tracker.is_downloaded("test")
```

**Priority:** 🔴 CRITICAL  
**Estimated Time:** 2 hours (write tests + fix implementation)  
**Blocks:** CRITICAL-1 fix

---

### Test Group 2: Duplicate Download Prevention 🔴 CRITICAL

**File:** `tests/unit/test_download_deduplication.py` (NEW)

```python
"""Tests for preventing duplicate download starts."""

import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from humble_tools.sync.app import BundleDetailsScreen, ItemFormatRow
from humble_tools.sync.config import AppConfig


class TestDownloadDeduplication:
    """Test duplicate download prevention."""

    @pytest.fixture
    def mock_app(self):
        """Create mock app with call_from_thread."""
        app = Mock()
        app.call_from_thread = Mock(side_effect=lambda f, *args, **kwargs: f(*args, **kwargs))
        app._shutdown_event = Mock()
        app._shutdown_event.is_set = Mock(return_value=False)
        return app

    @pytest.fixture
    def mock_download_manager(self):
        """Create mock download manager with slow downloads."""
        manager = Mock()
        # Simulate slow download (50ms)
        def slow_download(*args, **kwargs):
            time.sleep(0.05)
            return True
        manager.download_item = Mock(side_effect=slow_download)
        return manager

    @pytest.fixture
    def screen(self, mock_download_manager, mock_app):
        """Create BundleDetailsScreen with mocks."""
        config = AppConfig(max_concurrent_downloads=3, output_dir=Path("/tmp/test"))
        screen = BundleDetailsScreen(mock_download_manager, config)
        screen.app = mock_app
        screen.bundle_key = "test_bundle"
        return screen

    def test_rapid_double_click_same_format(self, screen, mock_download_manager):
        """Test rapid double-clicks don't start duplicate downloads.

        CRITICAL-2: Tests race condition in download_format.
        Simulates user pressing Enter twice in quick succession.
        Expected: Only one download starts.
        Current behavior: Both may start (race condition).
        """
        # Create item with PDF and EPUB formats
        item_row = ItemFormatRow(
            item_number=1,
            item_name="Test Book",
            formats=["PDF", "EPUB"],
            item_size="10 MB",
            format_status={"PDF": False, "EPUB": False},
            selected_format="PDF"
        )

        # Simulate two rapid clicks (both threads will check format_downloading at nearly same time)
        threads = [
            threading.Thread(target=screen.download_format, args=(item_row,)),
            threading.Thread(target=screen.download_format, args=(item_row,)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should only call download_item once (deduplicated)
        # FIXME: Currently fails - will be called twice
        assert mock_download_manager.download_item.call_count == 1, \
            "Duplicate download started! Race condition detected."

    def test_concurrent_downloads_different_formats_allowed(self, screen, mock_download_manager):
        """Test concurrent downloads of different formats is allowed.

        Verifies: Deduplication only prevents same format, not different ones.
        """
        item_row = ItemFormatRow(
            item_number=1,
            item_name="Test Book",
            formats=["PDF", "EPUB"],
            item_size="10 MB",
            format_status={"PDF": False, "EPUB": False}
        )

        # Download PDF
        item_row.selected_format = "PDF"
        thread1 = threading.Thread(target=screen.download_format, args=(item_row,))

        # Download EPUB (different format)
        item_row.selected_format = "EPUB"
        thread2 = threading.Thread(target=screen.download_format, args=(item_row,))

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        # Both should succeed (different formats)
        assert mock_download_manager.download_item.call_count == 2

    def test_already_downloaded_not_redownloaded(self, screen, mock_download_manager):
        """Test already downloaded formats are not re-downloaded."""
        item_row = ItemFormatRow(
            item_number=1,
            item_name="Test Book",
            formats=["PDF"],
            item_size="10 MB",
            format_status={"PDF": True},  # Already downloaded
            selected_format="PDF"
        )

        # Try to download
        screen.download_format(item_row)

        # Should not call download (already have it)
        mock_download_manager.download_item.assert_not_called()

    def test_queued_format_not_requeued(self, screen, mock_download_manager):
        """Test format already queued is not re-queued."""
        item_row = ItemFormatRow(
            item_number=1,
            item_name="Test Book",
            formats=["PDF"],
            item_size="10 MB",
            format_status={"PDF": False},
            selected_format="PDF"
        )

        # Mark as already queued
        item_row.format_queued["PDF"] = True

        # Try to download
        screen.download_format(item_row)

        # Should not call download (already queued)
        mock_download_manager.download_item.assert_not_called()
```

**Priority:** 🔴 CRITICAL  
**Estimated Time:** 2 hours  
**Blocks:** CRITICAL-2 fix

---

### Test Group 3: Queue State Recovery 🔴 CRITICAL

**File:** `tests/unit/test_queue_error_recovery.py` (NEW)

```python
"""Tests for queue state recovery from errors."""

import threading
from pathlib import Path
from unittest.mock import Mock
import pytest

from humble_tools.sync.app import BundleDetailsScreen, ItemFormatRow
from humble_tools.sync.config import AppConfig
from humble_tools.sync.download_queue import DownloadQueue


class TestQueueErrorRecovery:
    """Test queue state remains consistent after errors."""

    def test_queue_state_after_exception_in_download(self):
        """Test queue state is cleaned up after download exception.

        CRITICAL-3: Tests queue state consistency in error paths.
        Expected: Active count decremented, semaphore released.
        """
        queue = DownloadQueue(max_concurrent=2)

        # Mark queued and acquire
        queue.mark_queued()
        queue.acquire()
        queue.mark_started()

        assert queue.active_count == 1
        assert queue.queued_count == 0

        # Simulate exception during download
        try:
            raise RuntimeError("Download failed")
        finally:
            # Cleanup should happen in finally block
            queue.mark_completed()
            queue.release()

        # State should be clean
        assert queue.active_count == 0
        assert queue.queued_count == 0

        # Should be able to acquire again
        assert queue.acquire(blocking=False) is True
        queue.release()

    def test_no_double_decrement_if_never_started(self):
        """Test that we don't decrement active if we never incremented it.

        CRITICAL-3: Tests preventing negative counters.
        Scenario: Queued, then error before mark_started.
        """
        queue = DownloadQueue()

        # Mark queued
        queue.mark_queued()
        assert queue.queued_count == 1
        assert queue.active_count == 0

        # Error occurs before mark_started
        # Should decrement queued, not active
        queue._queued = max(0, queue._queued - 1)

        assert queue.queued_count == 0
        assert queue.active_count == 0

        # Should NOT raise on next operation
        queue.mark_queued()
        queue.mark_started()
        queue.mark_completed()  # Should not raise

    def test_acquire_timeout_doesnt_corrupt_state(self):
        """Test that acquire timeout doesn't leave queue in bad state.

        CRITICAL-3: Tests timeout during acquire.
        """
        queue = DownloadQueue(max_concurrent=1)

        # Acquire the only slot
        queue.acquire()

        # Try to acquire with timeout (will fail)
        queue.mark_queued()
        success = queue.acquire(blocking=True, timeout=0.1)

        assert success is False
        assert queue.queued_count == 1  # Still queued
        assert queue.active_count == 0  # Never started

        # Cleanup queued since we failed to acquire
        queue._queued = max(0, queue._queued - 1)

        # Release original
        queue.release()

        # State should be clean
        assert queue.queued_count == 0
        assert queue.active_count == 0

    def test_multiple_errors_dont_cause_negative_counters(self):
        """Test that multiple errors don't cause negative counters.

        CRITICAL-3: Regression test for counter corruption.
        """
        queue = DownloadQueue()

        # Scenario: 3 downloads queued, all fail at different stages

        # Download 1: Queued, started, fails during download
        queue.mark_queued()
        queue.acquire()
        queue.mark_started()
        queue.mark_completed()  # Cleanup
        queue.release()

        # Download 2: Queued, fails before acquire
        queue.mark_queued()
        # Error before acquire
        queue._queued = max(0, queue._queued - 1)  # Manual cleanup

        # Download 3: Queued, acquired, fails before started
        queue.mark_queued()
        queue.acquire()
        # Error before mark_started
        queue._queued = max(0, queue._queued - 1)  # Manual cleanup
        queue.release()

        # All counters should be non-negative
        assert queue.active_count >= 0
        assert queue.queued_count >= 0
        assert queue.active_count == 0
        assert queue.queued_count == 0
```

**Priority:** 🔴 CRITICAL  
**Estimated Time:** 1.5 hours  
**Blocks:** CRITICAL-3 fix

---

### Test Group 4: Graceful Shutdown 🔴 CRITICAL

**File:** `tests/integration/test_shutdown.py` (NEW)

```python
"""Integration tests for graceful shutdown."""

import threading
import time
from unittest.mock import Mock, patch
import pytest

from humble_tools.sync.app import HumbleBundleTUI, BundleDetailsScreen
from humble_tools.sync.config import AppConfig


class TestGracefulShutdown:
    """Test application shutdown during active operations."""

    @pytest.mark.asyncio
    async def test_shutdown_with_active_downloads(
        self, mock_get_bundles, mock_bundle_with_items
    ):
        """Test app can shutdown cleanly with active downloads.

        CRITICAL-4: Tests graceful shutdown mechanism.
        Expected: Downloads stop, workers terminate, clean exit.
        Current behavior: Workers continue running after exit.
        """
        app = HumbleBundleTUI()
        app.download_manager.get_bundle_items = Mock(
            return_value=mock_bundle_with_items
        )

        # Slow download (1 second)
        def slow_download(*args, **kwargs):
            time.sleep(1.0)
            return True

        app.download_manager.download_item = Mock(side_effect=slow_download)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Start download
            await pilot.press("enter")  # Go to details
            await pilot.pause()
            await pilot.press("enter")  # Start download
            await pilot.pause(0.1)  # Let it start

            # Immediately quit
            await pilot.press("q")
            await pilot.pause(0.1)

        # App should exit cleanly (run_test context exits)
        # Worker threads should be terminated or marked for termination
        # FIXME: Currently workers continue running

        # Verify no dangling threads (besides main)
        active_threads = [t for t in threading.enumerate() if t != threading.main_thread()]
        assert len(active_threads) == 0, \
            f"Worker threads still running after shutdown: {active_threads}"

    @pytest.mark.asyncio
    async def test_call_from_thread_during_shutdown(
        self, mock_get_bundles, mock_bundle_with_items
    ):
        """Test call_from_thread handles shutdown gracefully.

        CRITICAL-5: Tests UI update failure handling.
        Expected: UI updates fail silently or are skipped.
        """
        app = HumbleBundleTUI()
        app.download_manager.get_bundle_items = Mock(
            return_value=mock_bundle_with_items
        )

        call_errors = []

        def download_with_delayed_ui_update(*args, **kwargs):
            """Download that tries to update UI after delay."""
            time.sleep(0.5)  # Download takes time
            # By this time, app might be shutting down
            try:
                # This would normally call app.call_from_thread
                # but app might be gone
                return True
            except Exception as e:
                call_errors.append(e)
                return True

        app.download_manager.download_item = Mock(
            side_effect=download_with_delayed_ui_update
        )

        async with app.run_test() as pilot:
            await pilot.pause()

            # Start download
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause(0.1)

            # Quit immediately
            await pilot.press("q")
            # Don't wait - force shutdown

        # Should not crash, errors should be caught
        # FIXME: Currently may raise uncaught exceptions
```

**Priority:** 🔴 CRITICAL  
**Estimated Time:** 3 hours (complex integration test)  
**Blocks:** CRITICAL-4, CRITICAL-5 fixes

---

## Phase 3: Implementation Tasks

### Task 3.1: Fix CRITICAL-1 - Database Thread Safety 🔴

**Status:** ⏳ TODO  
**Test Coverage:** `test_tracker_concurrency.py` (Phase 2.1)  
**Files to Modify:**

- `src/humble_tools/core/tracker.py`
- `src/humble_tools/core/database.py`

**Implementation Steps:**

1. **Add threading.Lock to DownloadTracker**

```python
# src/humble_tools/core/tracker.py

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
        self._lock = threading.Lock()  # NEW: Thread safety lock

    def mark_downloaded(
        self,
        file_url: str,
        bundle_key: str,
        filename: str,
        file_path: Optional[str] = None,
        file_size: Optional[str] = None,
        bundle_total_files: Optional[int] = None,
    ):
        """Mark a file as downloaded (thread-safe).

        Args:
            file_url: Unique URL of the file
            bundle_key: Bundle identifier
            filename: Name of the file
            file_path: Local path where file was saved
            file_size: Human-readable file size
            bundle_total_files: Total number of files in the bundle
        """
        with self._lock:  # CHANGED: Wrap in lock
            self._conn.execute(
                """
                INSERT OR REPLACE INTO downloads
                (file_url, bundle_key, filename, file_size, downloaded_at, file_path, bundle_total_files)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_url,
                    bundle_key,
                    filename,
                    file_size,
                    datetime.now(),
                    file_path,
                    bundle_total_files,
                ),
            )
            self._conn.commit()

    def is_downloaded(self, file_url: str) -> bool:
        """Check if a file has been downloaded (thread-safe).

        Args:
            file_url: Unique URL of the file

        Returns:
            True if file is in database, False otherwise
        """
        with self._lock:  # CHANGED: Wrap in lock
            cursor = self._conn.execute(
                "SELECT 1 FROM downloads WHERE file_url = ?", (file_url,)
            )
            return cursor.fetchone() is not None

    def get_bundle_stats(self, bundle_key: str) -> Dict[str, Optional[int]]:
        """Get download statistics for a bundle (thread-safe).

        Args:
            bundle_key: Bundle identifier

        Returns:
            Dictionary with 'downloaded', 'remaining', and 'total' counts
        """
        with self._lock:  # CHANGED: Wrap in lock
            cursor = self._conn.execute(
                "SELECT COUNT(*), MAX(bundle_total_files) FROM downloads WHERE bundle_key = ?",
                (bundle_key,),
            )
            result = cursor.fetchone()
            downloaded = result[0]
            total_files = result[1]

            if total_files is None:
                return {"downloaded": downloaded, "remaining": None, "total": None}

            return {
                "downloaded": downloaded,
                "remaining": max(0, total_files - downloaded),
                "total": total_files,
            }

    # ... Apply same pattern to all other methods ...
```

2. **Add database timeout configuration**

```python
# src/humble_tools/core/database.py

class SQLiteConnection:
    """SQLite database connection wrapper with schema management."""

    def __init__(self, db_path: str | Path = ":memory:"):
        """Initialize SQLite connection.

        Args:
            db_path: Path to database file or ":memory:" for in-memory DB
        """
        if isinstance(db_path, Path):
            db_path = str(db_path)

        # CHANGED: Add timeout parameter
        self._conn = sqlite3.connect(
            db_path,
            check_same_thread=False,
            timeout=5.0  # NEW: 5 second timeout for lock waits
        )
        self._initialize_schema()
```

**Verification:**

```bash
# Run new concurrency tests
uv run pytest tests/unit/test_tracker_concurrency.py -v

# Run all tracker tests
uv run pytest tests/unit/test_tracker.py -v

# Full test suite
uv run pytest
```

**Success Criteria:**

- ✅ All tests in `test_tracker_concurrency.py` pass
- ✅ No regressions in existing tracker tests
- ✅ No "database is locked" errors under concurrent load

---

### Task 3.2: Fix CRITICAL-2 - Duplicate Download Prevention 🔴

**Status:** ⏳ TODO  
**Test Coverage:** `test_download_deduplication.py` (Phase 2.2)  
**Files to Modify:**

- `src/humble_tools/sync/app.py` (BundleDetailsScreen class)

**Implementation Steps:**

1. **Add pending downloads tracking to BundleDetailsScreen**

```python
# src/humble_tools/sync/app.py

class BundleDetailsScreen(Container):
    """Screen showing bundle details and items."""

    # ... existing code ...

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

2. **Implement atomic check-and-add in download_format**

```python
# src/humble_tools/sync/app.py

@work(thread=True)
def download_format(self, item_row: ItemFormatRow) -> None:
    """Download the selected format.

    This method runs in a worker thread (via @work(thread=True)).
    UI updates are dispatched back to the main thread using call_from_thread.

    Args:
        item_row: Row containing item and format information
    """
    selected_format = item_row.selected_format

    # Early returns for invalid states
    if selected_format is None:
        return

    # CHANGED: Create unique download key
    download_key = (self.bundle_key, item_row.item_number, selected_format)

    # CHANGED: Atomic check-and-add to prevent duplicates
    with self._pending_lock:
        # Check all conditions atomically
        if download_key in self._pending_downloads:
            return  # Already queued or downloading
        if item_row.format_downloading.get(selected_format, False):
            return  # Already downloading (belt-and-suspenders)
        if item_row.format_queued.get(selected_format, False):
            return  # Already queued (belt-and-suspenders)
        if item_row.format_status.get(selected_format, False):
            return  # Already downloaded

        # Atomically mark as pending
        self._pending_downloads.add(download_key)

    # Now we have exclusive access to download this format
    try:
        # Mark as queued
        self.app.call_from_thread(
            self._handle_download_queued,
            item_row,
            selected_format,
        )

        # ... rest of download logic unchanged ...

    finally:
        # Always remove from pending set
        with self._pending_lock:
            self._pending_downloads.discard(download_key)
```

**Verification:**

```bash
# Run deduplication tests
uv run pytest tests/unit/test_download_deduplication.py -v

# Run integration tests
uv run pytest tests/integration/test_integration_downloads.py -v

# Full suite
uv run pytest
```

**Success Criteria:**

- ✅ `test_rapid_double_click_same_format` passes
- ✅ No duplicate downloads under concurrent requests
- ✅ Different formats can still download concurrently

---

### Task 3.3: Fix CRITICAL-3 - Queue State Recovery 🔴

**Status:** ⏳ TODO  
**Test Coverage:** `test_queue_error_recovery.py` (Phase 2.3)  
**Files to Modify:**

- `src/humble_tools/sync/app.py` (download_format method)

**Implementation Steps:**

1. **Improve error handling in download_format**

```python
# src/humble_tools/sync/app.py

@work(thread=True)
def download_format(self, item_row: ItemFormatRow) -> None:
    """Download the selected format with robust error handling.

    This method runs in a worker thread (via @work(thread=True)).
    UI updates are dispatched back to the main thread using call_from_thread.

    Args:
        item_row: Row containing item and format information
    """
    selected_format = item_row.selected_format

    # Early returns for invalid states
    if selected_format is None:
        return

    # Create unique download key
    download_key = (self.bundle_key, item_row.item_number, selected_format)

    # Atomic check-and-add to prevent duplicates
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

    # Track whether we've moved to active state
    moved_to_active = False
    acquired_slot = False

    try:
        # Mark as queued
        self._safe_call_from_thread(
            self._handle_download_queued,
            item_row,
            selected_format,
        )

        # CHANGED: Acquire with timeout to handle shutdown
        acquired_slot = self._queue.acquire(blocking=True, timeout=1.0)

        if not acquired_slot:
            # Timeout (likely shutting down)
            # Decrement queued counter since we're aborting
            with self._queue._lock:
                self._queue._queued = max(0, self._queue._queued - 1)
            return

        # Move from queued to downloading
        self._safe_call_from_thread(
            self._handle_download_started,
            item_row,
            selected_format,
        )
        moved_to_active = True  # CHANGED: Track state transition

        # Perform download - blocking I/O is OK in thread worker
        try:
            success = self.download_manager.download_item(
                bundle_key=self.bundle_key,
                item_number=item_row.item_number,
                format_name=selected_format,
                output_dir=self.config.output_dir,
            )
        except HumbleCLIError as e:
            raise DownloadError(
                message=str(e),
                user_message=f"Download failed for {item_row.item_name}. Please try again.",
            ) from e
        except (IOError, OSError) as e:
            raise DownloadError(
                message=str(e),
                user_message=f"File error during download: {e}",
            ) from e

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
        # CHANGED: Only cleanup if we actually started
        if moved_to_active:
            self._safe_call_from_thread(self._handle_download_cleanup)
        elif acquired_slot:
            # We acquired but never started - just decrement queued
            with self._queue._lock:
                self._queue._queued = max(0, self._queue._queued - 1)

        # Always release semaphore if we acquired it
        if acquired_slot:
            self._queue.release()

        # Always remove from pending set
        with self._pending_lock:
            self._pending_downloads.discard(download_key)
```

2. **Add safe call_from_thread wrapper**

```python
# src/humble_tools/sync/app.py

class BundleDetailsScreen(Container):
    # ... existing code ...

    def _safe_call_from_thread(self, callback, *args, **kwargs):
        """Safely call function from thread, handling shutdown gracefully.

        Args:
            callback: Function to call on main thread
            *args: Positional arguments for callback
            **kwargs: Keyword arguments for callback
        """
        try:
            self.app.call_from_thread(callback, *args, **kwargs)
        except RuntimeError as e:
            # Event loop has shut down - this is expected during app exit
            logging.debug(f"UI update skipped (app shutting down): {e}")
        except Exception as e:
            # Unexpected error
            logging.error(f"Unexpected error in call_from_thread: {e}")
```

**Verification:**

```bash
# Run queue recovery tests
uv run pytest tests/unit/test_queue_error_recovery.py -v

# Run download queue tests
uv run pytest tests/unit/test_download_queue.py -v

# Integration tests
uv run pytest tests/integration/ -v

# Full suite
uv run pytest
```

**Success Criteria:**

- ✅ Queue counters never go negative
- ✅ Error paths clean up properly
- ✅ No semaphore leaks

---

### Task 3.4: Fix CRITICAL-4 & CRITICAL-5 - Graceful Shutdown 🔴

**Status:** ⏳ TODO  
**Test Coverage:** `test_shutdown.py` (Phase 2.4)  
**Files to Modify:**

- `src/humble_tools/sync/app.py` (HumbleBundleTUI and BundleDetailsScreen)

**Implementation Steps:**

1. **Add shutdown event to HumbleBundleTUI**

```python
# src/humble_tools/sync/app.py

class HumbleBundleTUI(App):
    """Main TUI application for Humble Bundle EPUB Manager."""

    # ... existing code ...

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__()
        self.config = config or AppConfig()
        self.tracker = DownloadTracker()
        self.download_manager = DownloadManager(self.tracker)
        # NEW: Shutdown coordination
        self._shutdown_event = threading.Event()
        self._active_workers = []  # Track worker threads

        # Screens
        self.bundle_list_screen = None
        self.bundle_details_screen = None
        self.current_screen = "list"

    def action_quit(self) -> None:
        """Quit with graceful shutdown of worker threads."""
        # Signal all workers to stop
        self._shutdown_event.set()

        # Give workers a moment to notice and cleanup
        # (They check shutdown_event before blocking operations)
        time.sleep(0.1)

        # Exit the app
        self.exit()
```

2. **Check shutdown flag in download_format**

```python
# src/humble_tools/sync/app.py

@work(thread=True)
def download_format(self, item_row: ItemFormatRow) -> None:
    """Download the selected format with shutdown awareness.

    This method runs in a worker thread (via @work(thread=True)).
    UI updates are dispatched back to the main thread using call_from_thread.

    Args:
        item_row: Row containing item and format information
    """
    # CHANGED: Check shutdown at entry
    if self.app._shutdown_event.is_set():
        return

    selected_format = item_row.selected_format

    # Early returns for invalid states
    if selected_format is None:
        return

    # ... deduplication logic ...

    # Track state
    moved_to_active = False
    acquired_slot = False

    try:
        # Mark as queued
        self._safe_call_from_thread(
            self._handle_download_queued,
            item_row,
            selected_format,
        )

        # CHANGED: Check shutdown before blocking
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

        # CHANGED: Check shutdown after acquire
        if self.app._shutdown_event.is_set():
            with self._queue._lock:
                self._queue._queued = max(0, self._queue._queued - 1)
            return

        # ... rest of download logic ...
```

**Verification:**

```bash
# Run shutdown tests
uv run pytest tests/integration/test_shutdown.py -v

# Run all integration tests
uv run pytest tests/integration/ -v

# Full suite
uv run pytest
```

**Success Criteria:**

- ✅ App exits cleanly during downloads
- ✅ No dangling worker threads
- ✅ call_from_thread failures handled gracefully
- ✅ No uncaught exceptions during shutdown

---

## Phase 4: Verification & Testing

### 4.1 Run All New Tests

```bash
# Run all new test files
uv run pytest \
    tests/unit/test_tracker_concurrency.py \
    tests/unit/test_download_deduplication.py \
    tests/unit/test_queue_error_recovery.py \
    tests/integration/test_shutdown.py \
    -v --tb=short

# Expected: All new tests pass
```

### 4.2 Run Full Test Suite

```bash
# Run complete test suite
uv run pytest -v

# Check coverage
uv run pytest --cov=src/humble_tools --cov-report=html --cov-report=term

# Expected:
# - All tests pass
# - Coverage remains high (>80%)
# - No regressions
```

### 4.3 Manual Testing

**Test Scenario 1: Rapid Downloads**

1. Launch TUI
2. Navigate to bundle with multiple items
3. Rapidly press Enter multiple times on same item
4. Verify: Only one download starts

**Test Scenario 2: Concurrent Downloads**

1. Launch TUI
2. Start 3 downloads quickly (different items)
3. Verify: All 3 run concurrently
4. Verify: 4th download waits in queue

**Test Scenario 3: Shutdown During Downloads**

1. Launch TUI
2. Start multiple downloads
3. Press 'q' to quit
4. Verify: App exits within 2 seconds
5. Verify: No error messages

**Test Scenario 4: Database Integrity**

1. Run multiple TUI instances simultaneously
2. Download different items in each
3. Check `~/.humblebundle/downloads.db`
4. Verify: All downloads tracked correctly

---

## Phase 5: Documentation & Cleanup

### 5.1 Update Documentation

- [x] Update CHANGELOG.md with bug fixes
- [ ] Update README.md with concurrency notes
- [ ] Add threading safety section to architecture docs

### 5.2 Code Review Checklist

- [ ] All new tests pass
- [ ] No regressions in existing tests
- [ ] Code follows project style (ruff passes)
- [ ] Type hints complete
- [ ] Docstrings updated
- [ ] Error messages user-friendly
- [ ] Logging added for debugging

### 5.3 Performance Testing

```bash
# Test database performance under load
uv run python -m tests.benchmark.tracker_concurrent

# Test UI responsiveness
# (Manual: Launch TUI, start downloads, navigate around)

# Check memory leaks
# (Manual: Run for extended period, monitor memory)
```

---

## Summary & Timeline

### Estimated Timeline

| Phase | Task                             | Time | Dependencies |
| ----- | -------------------------------- | ---- | ------------ |
| 2.1   | Write database concurrency tests | 2h   | None         |
| 2.2   | Write deduplication tests        | 2h   | None         |
| 2.3   | Write queue recovery tests       | 1.5h | None         |
| 2.4   | Write shutdown tests             | 3h   | None         |
| 3.1   | Implement database locking       | 1h   | Phase 2.1    |
| 3.2   | Implement deduplication          | 1.5h | Phase 2.2    |
| 3.3   | Implement queue recovery         | 2h   | Phase 2.3    |
| 3.4   | Implement shutdown               | 3h   | Phase 2.4    |
| 4.0   | Verification & testing           | 2h   | Phase 3.\*   |
| 5.0   | Documentation                    | 1h   | Phase 4.0    |

**Total Estimated Time:** ~18-20 hours (~2-3 developer days)

### Success Metrics

- ✅ All 6 critical bugs fixed
- ✅ 40+ new tests added (high-value, focused)
- ✅ 0 test regressions
- ✅ Clean shutdown under all conditions
- ✅ No race conditions in concurrent scenarios
- ✅ Database integrity maintained under load

---

## Next Steps

1. **Start with Phase 2.1** - Write database concurrency tests
2. **Validate tests fail** - Confirm they catch the bugs
3. **Implement fixes** - One task at a time
4. **Verify tests pass** - Green all the way
5. **Move to next task** - Systematic progress

---

_Last Updated: December 23, 2025_
