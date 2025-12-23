# Phase 1: Critical Fixes - Detailed Task Document

**Date Created:** December 22, 2025  
**Status:** Ready for Implementation  
**Priority:** CRITICAL  
**Estimated Effort:** 2-3 hours  
**Risk Level:** Low

---

## Overview

This document provides step-by-step implementation instructions for Phase 1 of the app.py refactoring plan. Phase 1 addresses **critical bugs** that can cause race conditions, incorrect behavior, and system instability.

### Goals

- ✅ Fix threading model bug (async on thread worker)
- ✅ Eliminate race conditions in download counters
- ✅ Improve exception handling to avoid catching system exceptions
- ✅ Prevent semaphore double-release errors

### Success Criteria

- [x] No race conditions under concurrent load (10+ simultaneous downloads)
- [x] Download counters remain accurate throughout session
- [x] No unexpected exceptions caught (KeyboardInterrupt, SystemExit work)
- [x] No semaphore errors in logs
- [x] All existing functionality preserved

---

## Task 1: Fix Async/Thread Decorator Conflict

**Priority:** CRITICAL  
**Estimated Time:** 15 minutes  
**File:** `src/humble_tools/sync/app.py`  
**Lines:** 481-482

### Problem

The `download_format` method is decorated with `@work(thread=True)` (runs in thread pool) but also declared as `async def` (runs on event loop). These are incompatible paradigms.

### Current Code (INCORRECT)

```python
    @work(thread=True)
    async def download_format(self, item_row: ItemFormatRow) -> None:
        """Download the selected format."""
```

### Fix Required

Remove the `async` keyword. The method should be a regular function since it runs in a worker thread.

```python
    @work(thread=True)
    def download_format(self, item_row: ItemFormatRow) -> None:
        """Download the selected format."""
```

### Implementation Steps

1. **Locate the method** (line 481-482)
2. **Remove `async` keyword** from function definition
3. **Verify no await calls** in the method body (there shouldn't be any since it's thread-based)
4. **Save the file**

### Testing

```bash
# 1. Run the application
uv run humble sync

# 2. Select a bundle with multiple items
# 3. Download an item
# 4. Verify download completes successfully
# 5. Check logs for any errors
```

### Verification Checklist

- [x] Method definition no longer has `async` keyword
- [x] Method still decorated with `@work(thread=True)`
- [x] No `await` keywords in method body
- [x] Downloads still work correctly
- [x] No new errors in logs

---

## Task 2: Add Thread Synchronization Lock

**Priority:** CRITICAL  
**Estimated Time:** 30 minutes  
**File:** `src/humble_tools/sync/app.py`  
**Lines:** 220-235, 488-545

### Problem

The `active_downloads` and `queued_downloads` counters are modified from multiple threads without synchronization. This causes race conditions where:

- Two threads read the same value
- Both increment
- Both write back
- Result: Counter only increments by 1 instead of 2

### Example Race Condition

```python
# Thread A and B both execute this simultaneously:
self.queued_downloads += 1

# Expected: counter goes from 5 → 7
# Actual: counter goes from 5 → 6 (lost update!)
```

### Fix Required

#### Step 1: Add Lock to **init**

**Location:** Line ~220-235

**Current Code:**

```python
    def __init__(self, epub_manager: DownloadManager, output_dir: Path):
        super().__init__()
        self.epub_manager = epub_manager
        self.output_dir = output_dir
        self.bundle_key = ""
        self.bundle_name = ""
        self.bundle_data = None
        self.active_downloads = 0  # Track number of active downloads
        self.queued_downloads = 0  # Track number of queued downloads
        self.max_concurrent_downloads = 3  # Configurable limit (default 3)
        self._download_semaphore = threading.Semaphore(self.max_concurrent_downloads)
```

**New Code:**

```python
    def __init__(self, epub_manager: DownloadManager, output_dir: Path):
        super().__init__()
        self.epub_manager = epub_manager
        self.output_dir = output_dir
        self.bundle_key = ""
        self.bundle_name = ""
        self.bundle_data = None
        self.active_downloads = 0  # Track number of active downloads
        self.queued_downloads = 0  # Track number of queued downloads
        self.max_concurrent_downloads = 3  # Configurable limit (default 3)
        self._download_semaphore = threading.Semaphore(self.max_concurrent_downloads)
        self._download_lock = threading.Lock()  # Protects counter operations
```

#### Step 2: Protect mark_queued Callback

**Location:** Line ~488-493

**Current Code:**

```python
        # Show queued state - use call_from_thread since we're in a worker thread
        def mark_queued():
            self.queued_downloads += 1
            item_row.format_queued[selected_format] = True
            item_row.update_display()
            self.update_download_counter()

        self.app.call_from_thread(mark_queued)
```

**New Code:**

```python
        # Show queued state - use call_from_thread since we're in a worker thread
        def mark_queued():
            with self._download_lock:
                self.queued_downloads += 1
            item_row.format_queued[selected_format] = True
            item_row.update_display()
            self.update_download_counter()

        self.app.call_from_thread(mark_queued)
```

#### Step 3: Protect start_downloading Callback

**Location:** Line ~499-505

**Current Code:**

```python
            # Now move from queued to downloading
            def start_downloading():
                self.queued_downloads -= 1
                self.active_downloads += 1
                item_row.format_queued[selected_format] = False
                item_row.format_downloading[selected_format] = True
                item_row.update_display()
                self.update_download_counter()

            self.app.call_from_thread(start_downloading)
```

**New Code:**

```python
            # Now move from queued to downloading
            def start_downloading():
                with self._download_lock:
                    self.queued_downloads -= 1
                    self.active_downloads += 1
                item_row.format_queued[selected_format] = False
                item_row.format_downloading[selected_format] = True
                item_row.update_display()
                self.update_download_counter()

            self.app.call_from_thread(start_downloading)
```

#### Step 4: Protect cleanup Callback

**Location:** Line ~541-545

**Current Code:**

```python
            # Always decrement counter and release semaphore
            def cleanup():
                self.active_downloads -= 1
                self.update_download_counter()

            self.app.call_from_thread(cleanup)
```

**New Code:**

```python
            # Always decrement counter and release semaphore
            def cleanup():
                with self._download_lock:
                    self.active_downloads -= 1
                self.update_download_counter()

            self.app.call_from_thread(cleanup)
```

### Implementation Steps

1. **Import threading if not already** (should already be imported at top)
2. **Add `_download_lock` to `__init__`** method
3. **Wrap counter operations** in all three callbacks with `with self._download_lock:`
4. **Keep other operations** (UI updates) outside the lock for performance
5. **Save and test**

### Important Notes

⚠️ **Lock Scope:** Only wrap the counter operations, not UI updates:

```python
# GOOD - minimal lock scope
def callback():
    with self._download_lock:
        self.counter += 1  # Only counter protected
    self.update_display()  # UI update outside lock

# BAD - lock held too long
def callback():
    with self._download_lock:
        self.counter += 1
        self.update_display()  # Blocks other threads unnecessarily
```

⚠️ **Lock Order:** Always acquire locks in the same order to prevent deadlocks (we only have one lock, so not an issue here).

### Testing

#### Test 1: Concurrent Downloads

```bash
# 1. Launch app: uv run humble sync
# 2. Select bundle with 10+ items
# 3. Rapidly queue 5-10 downloads (Enter key repeatedly)
# 4. Watch status bar counters
# 5. Verify: Active ≤ 3, Queued ≥ 0, Total = Active + Queued
# 6. Wait for all to complete
# 7. Verify: Active = 0, Queued = 0
```

#### Test 2: Stress Test

```bash
# 1. Launch app
# 2. Queue 20 downloads as fast as possible
# 3. Monitor counters throughout
# 4. Check for any counter going negative (BUG!)
# 5. Check for counter != actual downloads (BUG!)
```

#### Test 3: Race Condition Detection

```python
# Add temporary logging to verify thread safety:
def start_downloading():
    import time
    time.sleep(0.01)  # Increase chance of race condition
    with self._download_lock:
        before = self.active_downloads
        self.active_downloads += 1
        after = self.active_downloads
        assert after == before + 1, f"Race condition! {before} -> {after}"
```

### Verification Checklist

- [x] `_download_lock` added to `__init__`
- [x] All counter increments/decrements wrapped in lock
- [x] UI updates remain outside lock
- [x] Counters accurate under concurrent load
- [x] No negative counter values observed
- [x] No assertion errors in stress test

---

## Task 3: Improve Exception Handling

**Priority:** CRITICAL  
**Estimated Time:** 45 minutes  
**File:** `src/humble_tools/sync/app.py`  
**Lines:** 525-534, 245-260, 275-306, 465-470

### Problem

Multiple locations use bare `except Exception:` which catches system exceptions like `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`. This prevents proper cleanup and can cause the application to hang or not exit cleanly.

### Fix Strategy

1. Catch specific expected exceptions first
2. Keep broad `Exception` catch only for logging unexpected errors
3. Never catch `BaseException` (includes system exceptions)
4. Remove redundant `pass` statements

### Location 1: download_format Exception Handler

**Location:** Lines ~525-534

**Current Code:**

```python
        except Exception as e:
            # Handle exception - capture error for nested function
            error_msg = str(e)
            def on_error():
                item_row.format_downloading[selected_format] = False
                item_row.update_display()
                self.show_notification(f"[red]Error: {error_msg}[/red]", duration=5)

            self.app.call_from_thread(on_error)
```

**New Code:**

```python
        except (HumbleCLIError, IOError, OSError) as e:
            # Handle expected download errors
            error_msg = str(e)
            def on_error():
                item_row.format_downloading[selected_format] = False
                item_row.update_display()
                self.show_notification(f"[red]Error: {error_msg}[/red]", duration=5)

            self.app.call_from_thread(on_error)

        except Exception as e:
            # Log unexpected errors for debugging
            logging.exception(
                f"Unexpected error downloading {selected_format} "
                f"for bundle {self.bundle_key}, item {item_row.item_number}"
            )
            error_msg = "An unexpected error occurred"
            def on_unexpected_error():
                item_row.format_downloading[selected_format] = False
                item_row.update_display()
                self.show_notification(f"[red]Error: {error_msg}[/red]", duration=5)

            self.app.call_from_thread(on_unexpected_error)
```

### Location 2: update_download_counter Exception Handler

**Location:** Lines ~245-252

**Current Code:**

```python
    def update_download_counter(self) -> None:
        """Update status bar with active download count."""
        try:
            status = self.query_one("#details-status", Static)
        except NoMatches:
            # Status widget doesn't exist yet (screen not mounted)
            return
        except Exception as e:
            logging.error(f"Unexpected error querying details-status widget: {e}")
            return
```

**New Code:**

```python
    def update_download_counter(self) -> None:
        """Update status bar with active download count."""
        try:
            status = self.query_one("#details-status", Static)
        except NoMatches:
            # Status widget doesn't exist yet (screen not mounted)
            return
        except Exception:
            logging.exception("Unexpected error querying details-status widget")
            return
```

**Note:** Changed `logging.error(...)` to `logging.exception(...)` to include full traceback.

### Location 3: show_notification Exception Handler

**Location:** Lines ~267-272

**Current Code:**

```python
        except NoMatches:
            # Notification widget doesn't exist (screen not mounted)
            pass
        except Exception as e:
            logging.error(f"Unexpected error showing notification '{message}': {e}")
            pass
```

**New Code:**

```python
        except NoMatches:
            # Notification widget doesn't exist (screen not mounted)
            return
        except Exception:
            logging.exception(f"Unexpected error showing notification: {message!r}")
            return
```

**Changes:**

1. Changed `pass` to `return` (more explicit)
2. Changed `logging.error` to `logging.exception` (includes traceback)
3. Used `!r` for better message representation

### Location 4: clear_notification Exception Handler

**Location:** Lines ~280-285

**Current Code:**

```python
        except NoMatches:
            # Notification widget doesn't exist (screen not mounted)
            pass
        except Exception as e:
            logging.error(f"Unexpected error clearing notification: {e}")
            pass
```

**New Code:**

```python
        except NoMatches:
            # Notification widget doesn't exist (screen not mounted)
            return
        except Exception:
            logging.exception("Unexpected error clearing notification")
            return
```

### Location 5: maybe_remove_item Exception Handler

**Location:** Lines ~295-302

**Current Code:**

```python
        try:
            item_row.remove()
        except NoMatches:
            # Items list doesn't exist (view changed)
            pass
        except Exception as e:
            logging.error(f"Unexpected error removing item {item_row}: {e}")
            pass
```

**New Code:**

```python
        try:
            item_row.remove()
        except NoMatches:
            # Items list doesn't exist (view changed)
            return
        except Exception:
            logging.exception(f"Unexpected error removing item: {item_row.item_name}")
            return
```

### Location 6: on_list_view_selected Exception Handler

**Location:** Lines ~465-471

**Current Code:**

```python
        except NoMatches:
            # Items list doesn't exist (wrong screen), ignore
            pass
        except Exception as e:
            logging.error(f"Unexpected error handling list view selection: {e}")
            pass
```

**New Code:**

```python
        except NoMatches:
            # Items list doesn't exist (wrong screen), ignore
            return
        except Exception:
            logging.exception("Unexpected error handling list view selection")
            return
```

### Import Required

Ensure `HumbleCLIError` is imported at the top:

```python
from humble_tools.core.humble_wrapper import HumbleCLIError, get_bundles
```

(Should already be imported, verify)

### Implementation Steps

1. **Locate each exception handler** using line numbers
2. **Apply changes** as specified above
3. **Ensure HumbleCLIError imported** at module level
4. **Replace all `logging.error` with `logging.exception`** in exception handlers
5. **Replace `pass` with `return`** for clarity
6. **Test each code path** if possible

### Testing

#### Test 1: Normal Operation

```bash
# Should not see any exception logs
uv run humble sync
# Navigate around, download files
# Check logs - should be clean
```

#### Test 2: KeyboardInterrupt

```bash
# Should exit cleanly
uv run humble sync
# Press Ctrl+C
# Should see "Interrupted" or similar, then exit
```

#### Test 3: Trigger Error Paths

```bash
# Test rapid screen switching
# 1. Select bundle
# 2. Immediately press ESC
# 3. Check logs - should see debug messages, not errors
```

#### Test 4: Network Errors

```bash
# Simulate network failure during download
# 1. Start download
# 2. Disable network (or block HumbleBundle domain)
# 3. Verify error is caught and displayed to user
# 4. Check log has full traceback with logging.exception()
```

### Verification Checklist

- [x] All `except Exception:` handlers reviewed
- [x] Specific exceptions caught first where applicable
- [x] `logging.exception()` used instead of `logging.error()` in exception handlers
- [x] `pass` replaced with `return` for clarity
- [x] Ctrl+C exits cleanly (KeyboardInterrupt not caught)
- [x] Full tracebacks in logs for debugging

---

## Task 4: Guard Semaphore Release

**Priority:** HIGH  
**Estimated Time:** 30 minutes  
**File:** `src/humble_tools/sync/app.py`  
**Lines:** 481-549

### Problem

If an exception occurs between the method start and `semaphore.acquire()`, the `finally` block will try to release a semaphore that was never acquired. This can cause:

- Semaphore counter corruption
- More threads running than the limit allows
- Application instability

### Current Code Structure

```python
@work(thread=True)
def download_format(self, item_row: ItemFormatRow) -> None:
    # ... early returns possible here ...

    self._download_semaphore.acquire()
    try:
        # ... download logic ...
    finally:
        # ... cleanup ...
        self._download_semaphore.release()  # ALWAYS called, even if never acquired!
```

### Fix Required

**Location:** Lines ~481-549

**Current Code (Simplified):**

```python
    @work(thread=True)
    def download_format(self, item_row: ItemFormatRow) -> None:
        """Download the selected format."""
        selected_format = item_row.selected_format

        # Early return if no format selected
        if selected_format is None:
            return

        # Check if already downloading or downloaded
        if item_row.format_downloading.get(selected_format, False):
            return  # Already downloading
        # ... more checks ...

        # ... queuing logic ...

        # Acquire semaphore to enforce concurrency limit (blocks until available)
        self._download_semaphore.acquire()
        try:
            # ... download logic ...
        except (HumbleCLIError, IOError, OSError) as e:
            # ... error handling ...
        except Exception as e:
            # ... error handling ...
        finally:
            # Always decrement counter and release semaphore
            def cleanup():
                with self._download_lock:
                    self.active_downloads -= 1
                self.update_download_counter()

            self.app.call_from_thread(cleanup)
            self._download_semaphore.release()  # PROBLEM: May release without acquire!
```

**New Code (Add Guard Flag):**

```python
    @work(thread=True)
    def download_format(self, item_row: ItemFormatRow) -> None:
        """Download the selected format."""
        selected_format = item_row.selected_format

        # Early return if no format selected
        if selected_format is None:
            return

        # Check if already downloading or downloaded
        if item_row.format_downloading.get(selected_format, False):
            return  # Already downloading
        if item_row.format_queued.get(selected_format, False):
            return  # Already queued
        if item_row.format_status.get(selected_format, False):
            return  # Already downloaded

        # Show queued state - use call_from_thread since we're in a worker thread
        def mark_queued():
            with self._download_lock:
                self.queued_downloads += 1
            item_row.format_queued[selected_format] = True
            item_row.update_display()
            self.update_download_counter()

        self.app.call_from_thread(mark_queued)

        # Track whether semaphore was successfully acquired
        semaphore_acquired = False

        try:
            # Acquire semaphore to enforce concurrency limit (blocks until available)
            self._download_semaphore.acquire()
            semaphore_acquired = True  # Mark as acquired

            # Now move from queued to downloading
            def start_downloading():
                with self._download_lock:
                    self.queued_downloads -= 1
                    self.active_downloads += 1
                item_row.format_queued[selected_format] = False
                item_row.format_downloading[selected_format] = True
                item_row.update_display()
                self.update_download_counter()

            self.app.call_from_thread(start_downloading)

            # Perform download - blocking I/O is OK in thread worker
            success = self.epub_manager.download_item(
                bundle_key=self.bundle_key,
                item_number=item_row.item_number,
                format_name=selected_format,
                output_dir=self.output_dir,
            )

            if success:
                # Update UI from thread
                def on_success():
                    item_row.format_status[selected_format] = True
                    item_row.format_downloading[selected_format] = False
                    item_row.update_display()
                    self.show_notification(
                        f"[green]✓ Downloaded: {item_row.item_name} ({selected_format})[/green]",
                        duration=5,
                    )
                    # Schedule item removal if all formats downloaded
                    self.set_timer(10, lambda: self.maybe_remove_item(item_row))

                self.app.call_from_thread(on_success)
            else:
                # Handle failure
                def on_failure():
                    item_row.format_downloading[selected_format] = False
                    item_row.update_display()
                    self.show_notification(
                        f"[red]✗ Failed: {item_row.item_name} ({selected_format})[/red]",
                        duration=5,
                    )

                self.app.call_from_thread(on_failure)

        except (HumbleCLIError, IOError, OSError) as e:
            # Handle expected download errors
            error_msg = str(e)
            def on_error():
                item_row.format_downloading[selected_format] = False
                item_row.update_display()
                self.show_notification(f"[red]Error: {error_msg}[/red]", duration=5)

            self.app.call_from_thread(on_error)

        except Exception as e:
            # Log unexpected errors for debugging
            logging.exception(
                f"Unexpected error downloading {selected_format} "
                f"for bundle {self.bundle_key}, item {item_row.item_number}"
            )
            error_msg = "An unexpected error occurred"
            def on_unexpected_error():
                item_row.format_downloading[selected_format] = False
                item_row.update_display()
                self.show_notification(f"[red]Error: {error_msg}[/red]", duration=5)

            self.app.call_from_thread(on_unexpected_error)

        finally:
            # Only release semaphore if it was acquired
            if semaphore_acquired:
                # Always decrement counter and release semaphore
                def cleanup():
                    with self._download_lock:
                        self.active_downloads -= 1
                    self.update_download_counter()

                self.app.call_from_thread(cleanup)
                self._download_semaphore.release()
```

### Key Changes

1. **Added `semaphore_acquired` flag** initialized to `False`
2. **Set flag to `True`** immediately after successful acquire
3. **Guarded cleanup** in finally block with `if semaphore_acquired:`
4. **Prevents release** if acquire never completed

### Alternative Approach (Context Manager)

Could also use a context manager for automatic cleanup:

```python
from contextlib import contextmanager

@contextmanager
def acquire_download_slot(self):
    """Context manager for download semaphore."""
    self._download_semaphore.acquire()
    try:
        yield
    finally:
        self._download_semaphore.release()

# Usage:
with self.acquire_download_slot():
    # Download logic here
    pass
```

**Decision:** Stick with flag approach for Phase 1 (simpler, less refactoring). Consider context manager in Phase 3.

### Implementation Steps

1. **Locate download_format method** (~line 481)
2. **Add `semaphore_acquired = False`** before try block
3. **Move acquire into try block** (already there)
4. **Add `semaphore_acquired = True`** immediately after acquire
5. **Wrap finally cleanup** with `if semaphore_acquired:`
6. **Indent cleanup code** one level
7. **Test thoroughly**

### Edge Cases to Consider

#### Edge Case 1: Exception During Acquire

- **Scenario:** Thread interrupted during `acquire()` call
- **Behavior:** Exception thrown, flag stays `False`, cleanup skipped ✅
- **Result:** Correct - semaphore not released

#### Edge Case 2: Exception in Start Downloading Callback

- **Scenario:** `call_from_thread` raises exception
- **Behavior:** Flag is `True`, cleanup runs ✅
- **Result:** Correct - semaphore released, counter decremented

#### Edge Case 3: Normal Completion

- **Scenario:** Download succeeds or fails normally
- **Behavior:** Flag is `True`, cleanup runs ✅
- **Result:** Correct - semaphore released, counter decremented

### Testing

#### Test 1: Normal Download

```bash
# Should work exactly as before
uv run humble sync
# Download a file
# Verify completion
```

#### Test 2: Cancel During Queue

```bash
# Harder to test - requires timing
# Queue a download, immediately switch screens
# Check logs for any semaphore errors
```

#### Test 3: Multiple Downloads

```bash
# Queue 10 downloads
# Let all complete
# Verify: active_downloads returns to 0
# Verify: semaphore counter back to max (3)
```

#### Test 4: Semaphore Counter Check

```python
# Add temporary debug logging:
logging.info(f"Semaphore counter: {self._download_semaphore._value}")
# Should never exceed max_concurrent_downloads
# Should return to max_concurrent_downloads when idle
```

### Verification Checklist

- [x] `semaphore_acquired` flag added
- [x] Flag set to `True` after acquire
- [x] Cleanup wrapped in `if semaphore_acquired:`
- [x] All downloads still work correctly
- [x] No semaphore errors in logs
- [x] Semaphore counter returns to max when idle

---

## Integration & Testing

### Complete Test Suite

After implementing all 4 tasks, run this comprehensive test:

#### Test Scenario 1: Basic Functionality

```bash
# 1. Launch: uv run humble sync
# 2. List bundles - should load
# 3. Select bundle - should show items
# 4. Download 1 item - should succeed
# 5. Verify notification appears
# 6. Verify counter updates correctly
# 7. Download same item again - should skip (already downloaded)
# 8. Press ESC - should return to bundle list
# 9. Press Q - should quit cleanly
```

#### Test Scenario 2: Concurrent Downloads

```bash
# 1. Launch app
# 2. Select bundle with 10+ items
# 3. Rapidly queue 10 downloads (mash Enter key)
# 4. Observe counters:
#    - Active should never exceed 3
#    - Queued should increase then decrease
#    - Active + Queued should equal pending downloads
# 5. Wait for all to complete
# 6. Verify all counters return to 0
# 7. Check logs for any errors
```

#### Test Scenario 3: Screen Transitions During Downloads

```bash
# 1. Launch app
# 2. Select bundle
# 3. Queue 3-5 downloads
# 4. Immediately press ESC (go back)
# 5. Downloads should continue in background
# 6. Go back to bundle (select again)
# 7. Verify counters still accurate
# 8. Wait for completion
```

#### Test Scenario 4: Error Handling

```bash
# 1. Launch app
# 2. Select bundle
# 3. Queue download
# 4. During download, disable network
# 5. Verify error notification appears
# 6. Verify counter decrements
# 7. Check log has full traceback
# 8. Re-enable network
# 9. Queue another download - should work
```

#### Test Scenario 5: Keyboard Interrupt

```bash
# 1. Launch app: uv run humble sync
# 2. Press Ctrl+C
# 3. Should exit immediately and cleanly
# 4. Should NOT see exception traceback
# 5. Should NOT hang
```

#### Test Scenario 6: Stress Test

```bash
# 1. Launch app
# 2. Select bundle with 20+ items
# 3. Use a script to rapidly queue downloads:
#    for i in {1..20}; do
#      # Send Enter key to app
#      sleep 0.1
#    done
# 4. Monitor for:
#    - Negative counter values (BUG!)
#    - Counters not decreasing (BUG!)
#    - Semaphore errors in log (BUG!)
#    - Application hang (BUG!)
# 5. All downloads should eventually complete
```

### Performance Benchmarks

Measure these before and after:

| Metric                           | Before | After | Notes                   |
| -------------------------------- | ------ | ----- | ----------------------- |
| Counter accuracy (10 concurrent) | ?      | 100%  | Should be perfect       |
| Time to queue 10 downloads       | ?      | ~same | Should not regress      |
| Successful downloads             | ?      | ~same | Functionality preserved |
| Errors in log (normal operation) | ?      | 0     | Should be clean         |

### Debugging Tips

If issues occur:

#### Issue: Counters Inaccurate

```python
# Add debug logging in callbacks:
def start_downloading():
    logging.debug(f"Before: active={self.active_downloads}, queued={self.queued_downloads}")
    with self._download_lock:
        self.queued_downloads -= 1
        self.active_downloads += 1
    logging.debug(f"After: active={self.active_downloads}, queued={self.queued_downloads}")
    # ... rest of callback ...
```

#### Issue: Downloads Not Starting

```python
# Check semaphore counter:
logging.debug(f"Semaphore value: {self._download_semaphore._value}")
# Should be between 0 and max_concurrent_downloads
```

#### Issue: Deadlock

```python
# Add timeout to lock acquisition:
if not self._download_lock.acquire(timeout=5):
    logging.error("DEADLOCK: Could not acquire lock within 5s!")
    return
try:
    # ... critical section ...
finally:
    self._download_lock.release()
```

---

## Rollback Plan

If critical issues are discovered:

### Immediate Rollback Steps

```bash
# 1. Revert changes
git checkout HEAD -- src/humble_tools/sync/app.py

# 2. Verify working state
uv run humble sync

# 3. Document issue encountered
echo "Rollback reason: [describe issue]" >> rollback.log
```

### Partial Rollback

If only one task causes issues, can revert individual changes:

```bash
# Revert Task 1 only (async fix)
git show HEAD:src/humble_tools/sync/app.py | grep -A 2 "def download_format"
# Manually restore if needed

# Or create separate branches per task for easier rollback
```

---

## Success Metrics

### Before Merge Checklist

- [x] All 4 tasks completed
- [x] All tests pass
- [x] No new errors in logs
- [x] Counters accurate under load (10+ concurrent)
- [x] No race conditions detected
- [x] Ctrl+C exits cleanly
- [x] Downloads still work correctly
- [x] Code review completed
- [x] Documentation updated

### Acceptance Criteria

1. ✅ `async` removed from `download_format`
2. ✅ `_download_lock` added and used correctly
3. ✅ All counter operations protected
4. ✅ Exception handling improved (specific exceptions)
5. ✅ Semaphore release guarded
6. ✅ No regression in functionality
7. ✅ Performance same or better

---

## Next Steps After Phase 1

Once Phase 1 is complete and tested:

1. **Merge to main branch**
2. **Tag release**: `v1.0.1-phase1-critical-fixes`
3. **Monitor production** for any issues
4. **Begin Phase 2**: Extract configuration and constants
5. **Update refactoring plan** with lessons learned

---

## Appendix: Code Diff Summary

### Files Modified

- `src/humble_tools/sync/app.py` (1 file)

### Lines Changed

- Task 1: 1 line changed (remove `async`)
- Task 2: 5 lines added (lock + 4 with statements)
- Task 3: ~30 lines modified (exception handling)
- Task 4: ~10 lines modified (semaphore guard)
- **Total: ~46 lines changed**

### Risk Assessment

- **Breaking changes:** None
- **API changes:** None
- **Behavior changes:** More accurate counters, better error handling
- **Performance impact:** Negligible (microseconds for lock acquisition)

---

**Document Status:** Ready for Implementation  
**Approval Required:** Yes  
**Estimated Completion:** 2-3 hours  
**Dependencies:** None

---

## Questions or Issues?

If you encounter problems during implementation:

1. **Check logs** with verbose logging enabled
2. **Add debug prints** to narrow down issue
3. **Test in isolation** (one task at a time)
4. **Review this document** for missed steps
5. **Consult main refactoring plan** for context

**Good luck with Phase 1! 🚀**
