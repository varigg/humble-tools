# Existing Integration Tests Analysis

**Date:** December 22, 2025  
**Analyzed By:** GitHub Copilot  
**Status:** Recommend Replacement

---

## Summary

The existing `tests/integration/` directory contains 3 test files (1,098 lines total) that are **outdated due to app refactoring** and should be replaced by the new Phase 7B integration tests.

---

## Files Analyzed

### 1. `test_sync_app.py` (401 lines)

**Status:** ❌ OUTDATED - Replace entirely

**Problems:**

- Uses old screen API: `.display` property doesn't exist
- Wrong constructor signature: `BundleDetailsScreen(manager, output_dir)`
  - Should be: `BundleDetailsScreen(manager, config)`
- Assumes screens have `.display` property to show/hide
- References `app.current_screen` with values `"list"` and `"details"`
  - Current app likely uses different screen management

**Content:**

- Widget unit tests (BundleItem, ItemFormatRow) - Should be unit tests
- Screen initialization tests - Outdated API
- TUI navigation tests - Outdated screen system
- Bundle list handling - Outdated assumptions

**Salvageable:** None (all covered by new plan or unit tests)

---

### 2. `test_concurrent_downloads.py` (369 lines)

**Status:** ⚠️ PARTIALLY VALUABLE - Extract 1 scenario

**Problems:**

- Same API issues as above (wrong constructors, `.display` property)
- Tests reference old screen attributes
- Long, slow tests (2+ second sleeps)

**Valuable Scenarios:**

1. ✅ **Concurrent downloads showing indicators** (`test_concurrent_downloads_with_slow_mock`)

   - Starts download on item 1 (shows ⏳)
   - While item 1 downloading, starts item 2 (shows ⏳)
   - Verifies both show indicators simultaneously
   - Checks `active_downloads == 2`
   - **Added to new plan as 6th download test**

2. ✅ **Download-then-navigate** (`test_download_then_navigate`)
   - Start download, immediately navigate with arrow keys
   - Reproduces specific bug: `TypeError: clear_notification() got unexpected keyword argument 'delay'`
   - **Already covered** by new plan's "navigation during download" test

**Salvageable:** Concurrent indicator scenario (already added to new plan)

---

### 3. `test_thread_safety.py` (328 lines)

**Status:** ❌ MISCLASSIFIED - Move to unit tests

**Problems:**

- These are **unit tests**, not integration tests
- Test locks/semaphores in isolation (no TUI context)
- Test `BundleDetailsScreen` constructor attributes
- Use threading directly, not actual async TUI operations

**Content:**

- Lock initialization tests
- Semaphore limit tests
- Counter increment/decrement thread safety
- Config usage tests
- Exception handling tests

**Salvageable:** Move entire file to `tests/unit/test_thread_safety.py`

---

## Comparison: Old vs New

| Aspect            | Old Tests                  | New Plan (Phase 7B)  |
| ----------------- | -------------------------- | -------------------- |
| **Total tests**   | ~30+ tests                 | 10 tests             |
| **Lines of code** | 1,098 lines                | ~400 lines (est.)    |
| **API version**   | Pre-refactor               | Current              |
| **Test type**     | Mixed (unit + integration) | Pure integration     |
| **Assertions**    | Many "should not crash"    | Concrete assertions  |
| **Run time**      | 30-60s (slow mocks)        | <20s target          |
| **Flakiness**     | High (timing-dependent)    | Low (focused pauses) |
| **Maintenance**   | High (outdated API)        | Low (current API)    |

---

## Specific API Mismatches

### Screen Management

```python
# OLD (doesn't work)
assert app.bundle_list_screen.display is True
assert app.bundle_details_screen.display is False
app.current_screen == "list"  # or "details"

# NEW (actual API)
app.current_screen == "bundles"  # or "details"
# Textual handles screen visibility internally
```

### Constructor Signatures

```python
# OLD (doesn't work)
screen = BundleDetailsScreen(mock_manager, output_dir)

# NEW (actual API)
screen = BundleDetailsScreen(mock_manager, config)
# config = AppConfig(output_dir=output_dir, max_concurrent_downloads=3)
```

### Screen Classes

```python
# OLD assumption: Screens are separate objects with .display
# NEW reality: BundleListScreen and BundleDetailsScreen are Containers
```

---

## Recommendation

### Replace Entirely

1. ✅ Delete `tests/integration/test_sync_app.py`
2. ✅ Delete `tests/integration/test_concurrent_downloads.py`
3. ✅ Move `tests/integration/test_thread_safety.py` → `tests/unit/`
4. ✅ Implement Phase 7B integration tests (replace existing files in `tests/integration/`)

### Why Replace Instead of Fix?

1. **API changed fundamentally** - Screen management completely different
2. **Wrong test classification** - Many are unit tests, not integration tests
3. **More work to fix** - Easier to write focused new tests than update 1,098 lines
4. **Better design** - New tests have concrete assertions, not just "shouldn't crash"
5. **Faster** - New tests target <20s vs old 30-60s

---

## Migration Checklist

After Phase 7B tests pass:

- [ ] Run old tests to confirm they fail (outdated API)
- [ ] Verify all 10 new integration tests pass
- [ ] Delete `tests/integration/test_sync_app.py`
- [ ] Delete `tests/integration/test_concurrent_downloads.py`
- [ ] Move `tests/integration/test_thread_safety.py` to `tests/unit/test_thread_safety.py`
- [ ] Remove empty `tests/integration/` directory
- [ ] Update CI/CD if it references old test paths

---

## Lessons Learned

1. **Integration tests age quickly** - API refactoring invalidated 1,098 lines
2. **Test classification matters** - Unit tests in integration directory cause confusion
3. **Concrete assertions > crash prevention** - New tests verify actual behavior
4. **Focused tests > comprehensive coverage** - 10 focused tests > 30 unfocused tests

---

**Conclusion:** The existing integration tests are outdated and should be replaced with the new Phase 7B integration test suite. One valuable scenario (concurrent download indicators) has been incorporated into the new plan.
