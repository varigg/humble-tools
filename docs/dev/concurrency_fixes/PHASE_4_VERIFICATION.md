# Phase 4: Verification & Testing

**Status:** ⏳ TODO  
**Duration:** 2 hours  
**Priority:** CRITICAL  
**Dependencies:** Phase 3 complete (all fixes implemented)

---

## Objective

Comprehensively verify that:

1. All critical bugs are fixed
2. All new tests pass
3. No regressions in existing functionality
4. Performance is acceptable
5. Code quality standards are met

---

## Task 4.1: Run New Test Suite

**Time:** 15 minutes  
**Status:** ⏳ TODO

### Commands

```bash
# Run all new test files together
uv run pytest \
    tests/unit/test_tracker_concurrency.py \
    tests/unit/test_download_deduplication.py \
    tests/unit/test_queue_error_recovery.py \
    tests/integration/test_shutdown.py \
    -v --tb=short

# Expected output:
# test_tracker_concurrency.py::test_concurrent_mark_downloaded_same_bundle PASSED
# test_tracker_concurrency.py::test_concurrent_read_write_race PASSED
# test_tracker_concurrency.py::test_concurrent_is_downloaded_checks PASSED
# test_download_deduplication.py::test_rapid_double_click_same_format PASSED
# test_download_deduplication.py::test_concurrent_downloads_different_formats_allowed PASSED
# test_download_deduplication.py::test_already_downloaded_not_redownloaded PASSED
# test_download_deduplication.py::test_queued_format_not_requeued PASSED
# test_queue_error_recovery.py::test_queue_state_after_exception_in_download PASSED
# test_queue_error_recovery.py::test_no_double_decrement_if_never_started PASSED
# test_queue_error_recovery.py::test_acquire_timeout_doesnt_corrupt_state PASSED
# test_queue_error_recovery.py::test_multiple_errors_dont_cause_negative_counters PASSED
# test_shutdown.py::test_shutdown_with_active_downloads PASSED
# test_shutdown.py::test_call_from_thread_during_shutdown PASSED
#
# =============== 14 passed in 5.2s ===============
```

### Success Criteria

- [ ] All 14 new tests pass
- [ ] No test failures
- [ ] No warnings about deprecated features
- [ ] Total execution time < 10 seconds

---

## Task 4.2: Run Full Test Suite

**Time:** 10 minutes  
**Status:** ⏳ TODO

### Commands

```bash
# Run complete test suite
uv run pytest -v

# Check test counts
uv run pytest --collect-only -q | tail -5

# Expected:
# 138 tests collected (was ~124, added 14)
```

### Success Criteria

- [ ] All 138+ tests pass
- [ ] No skipped tests (unless expected)
- [ ] No flaky tests (run 3 times if needed)
- [ ] Total execution time < 30 seconds

### If Any Tests Fail

1. **Identify the failure**

   ```bash
   uv run pytest --lf -v  # Run last failed
   ```

2. **Check if it's a regression**

   ```bash
   git stash  # Stash changes
   uv run pytest <failing_test>  # Test passes without changes?
   git stash pop
   ```

3. **Debug the issue**

   ```bash
   uv run pytest <failing_test> -vv -s  # Verbose output
   ```

4. **Fix and re-verify**
   - Fix the issue
   - Run failing test
   - Run related tests
   - Run full suite

---

## Task 4.3: Code Coverage Analysis

**Time:** 15 minutes  
**Status:** ⏳ TODO

### Commands

```bash
# Generate coverage report
uv run pytest \
    --cov=src/humble_tools \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-report=term:skip-covered

# View HTML report
open htmlcov/index.html  # or: xdg-open htmlcov/index.html
```

### Coverage Targets

**Before Fixes:**

```
tracker.py:          90%
download_queue.py:   85%
app.py:              75%
Overall:             82%
```

**After Fixes:**

```
tracker.py:          95% (+5%)   # Added thread safety
download_queue.py:   90% (+5%)   # Better error handling
app.py:              80% (+5%)   # Shutdown + deduplication
Overall:             85% (+3%)
```

### Success Criteria

- [ ] Overall coverage ≥ 85%
- [ ] No new uncovered critical paths
- [ ] Concurrency code well-covered (≥ 80%)
- [ ] Error handling paths covered (≥ 70%)

---

## Task 4.4: Code Quality Checks

**Time:** 10 minutes  
**Status:** ⏳ TODO

### Linting

```bash
# Run ruff linter
uv run ruff check src/ tests/

# Expected: No errors
# (Warnings are acceptable if documented)
```

### Formatting

```bash
# Check formatting
uv run ruff format --check src/ tests/

# If issues found, auto-fix:
uv run ruff format src/ tests/
```

### Type Checking (Optional)

```bash
# Run type checker if configured
uv run mypy src/humble_tools/
# or
uv run pyright src/humble_tools/
```

### Success Criteria

- [ ] No ruff errors
- [ ] No formatting issues
- [ ] No new type: ignore comments added
- [ ] No TODO comments in production code

---

## Task 4.5: Performance Testing

**Time:** 20 minutes  
**Status:** ⏳ TODO

### Database Performance

```bash
# Create simple benchmark script
cat > benchmark_db.py << 'EOF'
import time
import threading
from humble_tools.core.tracker import DownloadTracker
from humble_tools.core.database import SQLiteConnection

def benchmark_concurrent_writes():
    """Benchmark concurrent database writes."""
    db = SQLiteConnection(":memory:")
    tracker = DownloadTracker(db_connection=db)

    start = time.time()

    def write_batch(start_idx):
        for i in range(100):
            tracker.mark_downloaded(
                f"url_{start_idx}_{i}",
                "bundle",
                f"file_{i}.epub"
            )

    threads = [
        threading.Thread(target=write_batch, args=(i*100,))
        for i in range(10)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    duration = time.time() - start
    print(f"1000 concurrent writes: {duration:.2f}s ({1000/duration:.0f} ops/sec)")

    db.close()

if __name__ == "__main__":
    benchmark_concurrent_writes()
EOF

# Run benchmark
uv run python benchmark_db.py

# Expected: < 2 seconds for 1000 writes
# (Lock overhead should be < 1ms per operation)
```

### UI Responsiveness Test

**Manual Test:**

1. Launch TUI: `uv run hb-epub tui`
2. Navigate to bundle with many items (30+)
3. Start multiple downloads (5+)
4. Navigate around while downloads active
5. Observe UI responsiveness

**Expected Behavior:**

- UI remains responsive (< 100ms lag)
- Can navigate while downloading
- Can quit cleanly
- No freezing

### Success Criteria

- [ ] Database operations < 2s for 1000 concurrent writes
- [ ] UI remains responsive during downloads
- [ ] Memory usage reasonable (< 100MB)
- [ ] No memory leaks over 5 minutes

---

## Task 4.6: Integration Testing

**Time:** 30 minutes  
**Status:** ⏳ TODO

### Manual Test Scenarios

#### Scenario 1: Rapid Downloads

```
1. Launch TUI
2. Navigate to bundle with items
3. Rapidly press Enter 5 times on same item
   → Expected: Only 1 download starts
   → Verify: No duplicate downloads
4. Check status bar shows correct count
   → Expected: "Active Downloads: 1/3"
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:**

---

#### Scenario 2: Concurrent Downloads

```
1. Launch TUI
2. Navigate to bundle
3. Quickly download 5 different items
   → Expected: 3 active, 2 queued
4. Wait for 1 to complete
   → Expected: Queued item starts automatically
5. Verify all complete successfully
   → Expected: 5 items marked as downloaded
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:**

---

#### Scenario 3: Shutdown During Downloads

```
1. Launch TUI
2. Start 3 downloads (will take ~5 seconds each)
3. Wait 1 second
4. Press 'q' to quit
   → Expected: App exits within 2 seconds
5. Check terminal for errors
   → Expected: Clean exit, no exceptions
6. Check process list
   → Expected: No dangling processes
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:**

---

#### Scenario 4: Database Integrity

```
1. Launch 2 TUI instances (different terminals)
2. In Instance 1: Download items from Bundle A
3. In Instance 2: Download items from Bundle B
4. Let both complete
5. Check ~/.humblebundle/downloads.db
   → Expected: All downloads tracked correctly
6. Query with sqlite3:
   SELECT COUNT(*) FROM downloads;
   → Expected: Correct count, no corruption
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:**

---

#### Scenario 5: Error Recovery

```
1. Launch TUI
2. Start download
3. Simulate network failure (disconnect)
   → Expected: Error message shown
4. Reconnect network
5. Retry download
   → Expected: Works correctly
6. Check queue state
   → Expected: Counters correct, no leaks
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:**

---

### Integration Test Success Criteria

- [ ] All 5 scenarios pass
- [ ] No crashes or exceptions
- [ ] User experience smooth
- [ ] Error messages clear and helpful
- [ ] Data integrity maintained

---

## Task 4.7: Regression Testing

**Time:** 15 minutes  
**Status:** ⏳ TODO

### Critical Workflows

```bash
# Test each major workflow still works

# 1. List bundles
uv run hb-epub tui
# Navigate, view list
# Expected: Bundles load correctly

# 2. View bundle details
# Press Enter on bundle
# Expected: Items shown with formats

# 3. Download single item
# Press Enter on item
# Wait for completion
# Expected: File downloaded, tracked

# 4. Navigate back and forth
# ESC to go back, Enter to go forward
# Expected: Navigation smooth

# 5. Quit application
# Press 'q'
# Expected: Clean exit
```

### Regression Checklist

- [ ] Bundle list loads
- [ ] Bundle details display correctly
- [ ] Single download works
- [ ] Multiple downloads work
- [ ] Format cycling works (←→ arrows)
- [ ] Navigation works (ESC, Enter)
- [ ] Quit works (q)
- [ ] Status messages display correctly
- [ ] Download tracking persists

---

## Task 4.8: Edge Cases Testing

**Time:** 15 minutes  
**Status:** ⏳ TODO

### Edge Cases to Test

#### Empty Bundle

```
1. Navigate to bundle with no items
   → Expected: "No items found" message
   → No crashes
```

#### Bundle with Only Keys (No Items)

```
1. Navigate to bundle with only game keys
   → Expected: Keys displayed in table
   → "No downloadable items" indicated
```

#### Very Large Bundle (50+ Items)

```
1. Navigate to large bundle
   → Expected: List scrolls correctly
   → Performance acceptable
   → Can download items
```

#### Rapid Quit

```
1. Launch TUI
2. Immediately press 'q' (before bundles load)
   → Expected: Clean exit
   → No "event loop closed" errors
```

#### Multiple Format Cycling

```
1. Select item with 3+ formats
2. Cycle through all formats multiple times
   → Expected: Cycles correctly
   → Selected format highlights properly
```

### Edge Case Checklist

- [ ] Empty bundle handled
- [ ] Keys-only bundle handled
- [ ] Large bundles (50+ items) work
- [ ] Rapid quit works
- [ ] Multiple format cycling works
- [ ] All edge cases handled gracefully

---

## Phase 4 Completion Checklist

### Test Verification

- [ ] All 14 new tests pass
- [ ] All existing tests pass (138+ total)
- [ ] No flaky tests
- [ ] No skipped tests (unless expected)

### Code Quality

- [ ] Coverage ≥ 85%
- [ ] Ruff linting passes
- [ ] Ruff formatting correct
- [ ] No new type: ignore needed
- [ ] No TODO comments left

### Performance

- [ ] Database operations fast (< 2s for 1000 writes)
- [ ] UI responsive during downloads
- [ ] No memory leaks
- [ ] Shutdown < 2 seconds

### Integration

- [ ] All 5 manual scenarios pass
- [ ] No regressions in critical workflows
- [ ] All edge cases handled
- [ ] User experience smooth

### Documentation

- [ ] Test results documented
- [ ] Any issues noted
- [ ] Performance metrics recorded

---

## Success Criteria

- ✅ 100% of new tests passing
- ✅ 100% of existing tests passing
- ✅ Code coverage ≥ 85%
- ✅ All quality checks pass
- ✅ Performance acceptable
- ✅ All manual scenarios pass
- ✅ No regressions found
- ✅ Ready for production

---

## Next Steps

If all checks pass:
→ Proceed to **[Phase 5: Documentation](PHASE_5_DOCUMENTATION.md)**

If issues found:
→ Return to **[Phase 3: Implementation](PHASE_3_IMPLEMENTATION.md)**  
→ Fix issues and re-run Phase 4

---

## Test Results Summary

**Date:** ******\_******  
**Tester:** ******\_******

| Category         | Tests Run | Passed | Failed | Notes |
| ---------------- | --------- | ------ | ------ | ----- |
| New Tests        | 14        |        |        |       |
| Existing Tests   | 124+      |        |        |       |
| Manual Scenarios | 5         |        |        |       |
| Edge Cases       | 5         |        |        |       |
| **Total**        | **148+**  |        |        |       |

**Overall Result:** [ ] PASS / [ ] FAIL

**Issues Found:**

1.
2.
3.

**Performance Notes:**

**Recommendations:**

---

_Phase 4 Status: TODO_
