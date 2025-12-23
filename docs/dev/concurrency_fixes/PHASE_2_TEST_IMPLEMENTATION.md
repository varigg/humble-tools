# Phase 2: High-Value Test Implementation

**Status:** ⏳ TODO  
**Duration:** 8 hours  
**Priority:** CRITICAL  
**Dependencies:** Phase 1 complete

---

## Objective

Create high-value tests that:

1. Demonstrate the critical bugs exist
2. Will verify fixes work correctly
3. Prevent future regressions

---

## Test Group 1: Database Concurrency 🔴

**File:** `tests/unit/test_tracker_concurrency.py`  
**Time:** 2 hours  
**Covers:** CRITICAL-1  
**Status:** ⏳ TODO

### Tests to Implement

#### Test 2.1.1: Concurrent Mark Downloaded

```python
def test_concurrent_mark_downloaded_same_bundle(self, tracker):
    """50 threads marking different files in same bundle.

    Expected to FAIL initially: database locked errors
    After fix: All 50 files marked successfully
    """
```

**What it tests:** Multiple threads writing to database simultaneously  
**Expected failure:** `sqlite3.OperationalError: database is locked`  
**Success after fix:** All 50 writes succeed, stats show 50 downloads

#### Test 2.1.2: Concurrent Read/Write Race

```python
def test_concurrent_read_write_race(self, tracker):
    """1 writer thread, 3 reader threads, continuous operations.

    Expected to FAIL initially: Inconsistent reads or corruption
    After fix: Reads always return valid data
    """
```

**What it tests:** SELECT queries during concurrent INSERT  
**Expected failure:** Reads return inconsistent data or errors  
**Success after fix:** All reads <= actual writes, no phantom reads

#### Test 2.1.3: Concurrent is_downloaded Checks

```python
def test_concurrent_is_downloaded_checks(self, tracker):
    """2 checker threads, 1 marker thread.

    Expected to FAIL initially: Database errors under contention
    After fix: All operations complete without errors
    """
```

**What it tests:** Concurrent reads during writes  
**Expected failure:** Database lock timeouts  
**Success after fix:** All operations complete successfully

### Implementation Checklist

- [ ] Create `tests/unit/test_tracker_concurrency.py`
- [ ] Add TestTrackerConcurrency class
- [ ] Implement test_concurrent_mark_downloaded_same_bundle
- [ ] Implement test_concurrent_read_write_race
- [ ] Implement test_concurrent_is_downloaded_checks
- [ ] Add test_database_timeout_handling (placeholder)
- [ ] Run tests and verify they FAIL as expected
- [ ] Document failure messages for comparison

### Expected Output (Before Fix)

```bash
$ uv run pytest tests/unit/test_tracker_concurrency.py -v

test_concurrent_mark_downloaded_same_bundle FAILED
  sqlite3.OperationalError: database is locked

test_concurrent_read_write_race FAILED
  AssertionError: Read returned value higher than written

test_concurrent_is_downloaded_checks FAILED
  sqlite3.OperationalError: database is locked
```

---

## Test Group 2: Download Deduplication 🔴

**File:** `tests/unit/test_download_deduplication.py`  
**Time:** 2 hours  
**Covers:** CRITICAL-2  
**Status:** ⏳ TODO

### Tests to Implement

#### Test 2.2.1: Rapid Double Click

```python
def test_rapid_double_click_same_format(self, screen, mock_download_manager):
    """Two threads start same download within milliseconds.

    Expected to FAIL initially: Both downloads start (race)
    After fix: Only one download starts
    """
```

**What it tests:** Check-then-act race condition  
**Expected failure:** `call_count == 2` (duplicate download)  
**Success after fix:** `call_count == 1` (deduplicated)

#### Test 2.2.2: Different Formats Allowed

```python
def test_concurrent_downloads_different_formats_allowed(self, screen):
    """PDF and EPUB downloads for same item concurrently.

    Should PASS initially: Different formats are allowed
    After fix: Still passes (no regression)
    """
```

**What it tests:** Deduplication only prevents same format  
**Expected behavior:** Both downloads start (no deduplication)  
**Success after fix:** Same behavior maintained

#### Test 2.2.3: Already Downloaded Check

```python
def test_already_downloaded_not_redownloaded(self, screen):
    """Try to download already downloaded format.

    Should PASS initially: Already has this check
    After fix: Still passes (no regression)
    """
```

**What it tests:** Early exit for completed downloads  
**Expected behavior:** No download started  
**Success after fix:** Same behavior maintained

#### Test 2.2.4: Already Queued Check

```python
def test_queued_format_not_requeued(self, screen):
    """Try to download already queued format.

    Expected to FAIL initially: Can queue twice
    After fix: Second attempt skipped
    """
```

**What it tests:** Duplicate queueing prevention  
**Expected failure:** Second download starts  
**Success after fix:** Second attempt skipped

### Implementation Checklist

- [ ] Create `tests/unit/test_download_deduplication.py`
- [ ] Add TestDownloadDeduplication class
- [ ] Implement test_rapid_double_click_same_format
- [ ] Implement test_concurrent_downloads_different_formats_allowed
- [ ] Implement test_already_downloaded_not_redownloaded
- [ ] Implement test_queued_format_not_requeued
- [ ] Run tests and verify expected failures
- [ ] Document race condition timing

### Expected Output (Before Fix)

```bash
$ uv run pytest tests/unit/test_download_deduplication.py -v

test_rapid_double_click_same_format FAILED
  AssertionError: Duplicate download started! Race condition detected.
  assert 2 == 1  (download_item called twice)

test_concurrent_downloads_different_formats_allowed PASSED
test_already_downloaded_not_redownloaded PASSED

test_queued_format_not_requeued FAILED
  AssertionError: Should not requeue
```

---

## Test Group 3: Queue State Recovery 🔴

**File:** `tests/unit/test_queue_error_recovery.py`  
**Time:** 1.5 hours  
**Covers:** CRITICAL-3  
**Status:** ⏳ TODO

### Tests to Implement

#### Test 2.3.1: Queue State After Exception

```python
def test_queue_state_after_exception_in_download():
    """Exception during download, verify cleanup in finally.

    Should PASS initially: Basic cleanup works
    After fix: Still passes with better error handling
    """
```

**What it tests:** Finally block cleanup  
**Expected behavior:** Counters reset correctly  
**Success after fix:** Same behavior with additional checks

#### Test 2.3.2: No Double Decrement

```python
def test_no_double_decrement_if_never_started():
    """Error before mark_started, verify correct cleanup.

    Expected to FAIL initially: May decrement wrong counter
    After fix: Only queued decremented, not active
    """
```

**What it tests:** State-aware cleanup  
**Expected failure:** Active goes negative  
**Success after fix:** Correct counter decremented

#### Test 2.3.3: Acquire Timeout

```python
def test_acquire_timeout_doesnt_corrupt_state():
    """Acquire times out, verify state remains valid.

    Expected to FAIL initially: Queued but never cleaned up
    After fix: Queued counter decremented on timeout
    """
```

**What it tests:** Timeout handling  
**Expected failure:** Queued counter permanently incremented  
**Success after fix:** Counter decremented on timeout

#### Test 2.3.4: Multiple Errors

```python
def test_multiple_errors_dont_cause_negative_counters():
    """Various error scenarios, verify counters never negative.

    Expected to FAIL initially: Some paths cause negative counts
    After fix: All counters remain >= 0
    """
```

**What it tests:** Comprehensive error handling  
**Expected failure:** Negative counters possible  
**Success after fix:** Counters always >= 0

### Implementation Checklist

- [ ] Create `tests/unit/test_queue_error_recovery.py`
- [ ] Add TestQueueErrorRecovery class
- [ ] Implement test_queue_state_after_exception_in_download
- [ ] Implement test_no_double_decrement_if_never_started
- [ ] Implement test_acquire_timeout_doesnt_corrupt_state
- [ ] Implement test_multiple_errors_dont_cause_negative_counters
- [ ] Run tests and verify expected failures
- [ ] Document error paths tested

### Expected Output (Before Fix)

```bash
$ uv run pytest tests/unit/test_queue_error_recovery.py -v

test_queue_state_after_exception_in_download PASSED
test_no_double_decrement_if_never_started FAILED
  RuntimeError: Cannot complete download: nothing active

test_acquire_timeout_doesnt_corrupt_state FAILED
  AssertionError: Queued counter not cleaned up: 1 != 0

test_multiple_errors_dont_cause_negative_counters FAILED
  AssertionError: Counter went negative: -1 >= 0
```

---

## Test Group 4: Graceful Shutdown 🔴

**File:** `tests/integration/test_shutdown.py`  
**Time:** 3 hours  
**Covers:** CRITICAL-4, CRITICAL-5  
**Status:** ⏳ TODO

### Tests to Implement

#### Test 2.4.1: Shutdown with Active Downloads

```python
async def test_shutdown_with_active_downloads():
    """Start downloads, immediately quit, verify clean exit.

    Expected to FAIL initially: Workers continue running
    After fix: Workers stop, clean exit
    """
```

**What it tests:** Worker thread termination  
**Expected failure:** Dangling threads after exit  
**Success after fix:** No threads except main

#### Test 2.4.2: call_from_thread During Shutdown

```python
async def test_call_from_thread_during_shutdown():
    """Download completes after app shutdown started.

    Expected to FAIL initially: Uncaught RuntimeError
    After fix: Error caught and logged
    """
```

**What it tests:** UI update failure handling  
**Expected failure:** Uncaught exception from call_from_thread  
**Success after fix:** Exception caught, no crash

### Implementation Checklist

- [ ] Create `tests/integration/test_shutdown.py`
- [ ] Add TestGracefulShutdown class
- [ ] Implement test_shutdown_with_active_downloads
- [ ] Implement test_call_from_thread_during_shutdown
- [ ] Add helper to check for dangling threads
- [ ] Run tests and verify expected failures
- [ ] Document shutdown timing issues

### Expected Output (Before Fix)

```bash
$ uv run pytest tests/integration/test_shutdown.py -v

test_shutdown_with_active_downloads FAILED
  AssertionError: Worker threads still running after shutdown
  Found 3 active threads: [<Thread(Thread-1)>, <Thread(Thread-2)>, ...]

test_call_from_thread_during_shutdown FAILED
  RuntimeError: Event loop is closed
```

---

## Phase 2 Completion Checklist

### Test Files Created

- [ ] `tests/unit/test_tracker_concurrency.py` (4 tests)
- [ ] `tests/unit/test_download_deduplication.py` (4 tests)
- [ ] `tests/unit/test_queue_error_recovery.py` (4 tests)
- [ ] `tests/integration/test_shutdown.py` (2 tests)

**Total: 14 new high-value tests**

### Verification Steps

- [ ] All new tests compile without syntax errors
- [ ] All new tests run (even if failing)
- [ ] Failure messages are clear and actionable
- [ ] No false positives (tests fail for right reasons)
- [ ] Test isolation verified (no interdependencies)

### Documentation

- [ ] Each test has docstring explaining what it tests
- [ ] Expected failures documented
- [ ] Success criteria documented
- [ ] Test output examples captured

---

## Success Criteria

- ✅ 14+ new tests created
- ✅ All tests demonstrate the bugs (fail as expected)
- ✅ Test failures are consistent and reproducible
- ✅ Clear path to fix shown by test expectations
- ✅ No false positives or flaky tests

---

## Next Steps

Proceed to **[Phase 3: Implementation](PHASE_3_IMPLEMENTATION.md)**

Start with Task 3.1: Fix CRITICAL-1 (Database Thread Safety)

---

## Notes

**Testing Philosophy:**

- Tests should fail loudly and clearly
- Test the bug, not the implementation
- Keep tests simple and focused
- One assertion per test when possible

**Common Pitfalls to Avoid:**

- Don't use excessive sleep() - use proper synchronization
- Don't make tests too complex - hard to debug
- Don't skip documentation - future you will thank you
- Don't ignore flaky tests - fix the root cause

---

_Phase 2 Status: TODO_
