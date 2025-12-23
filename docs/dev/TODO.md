# TODO List - Humble Bundle EPUB Manager Refactoring

**Last Updated**: December 7, 2025

---

## 🔴 High Priority - Do Next

_No high-priority tasks remaining. Move to medium priority._

---

## 🟡 Medium Priority - Do After High Priority

### 2. Add Status Update Helper to TUI

**File**: `src/humblebundle_epub/tui.py`  
**Status**: ⏸️ Ready to start

**Tasks**:

- [ ] Create `_update_status(message: str, style: str = "white") -> None`
- [ ] Replace 2 duplicated status update blocks (lines 341-343, 361-363)
- [ ] Test manually that status updates still work

**Estimated Effort**: 30 minutes  
**Impact**: Low - Removes small duplication  
**Risk**: Low

---

### 2. Complete Return Type Hints

**Files**: Multiple  
**Status**: ⏸️ Ready to start

**Tasks**:

- [ ] Add type hints to remaining TUI methods
- [ ] Add type hints to display functions
- [ ] Add type hints to tracker methods
- [ ] Run mypy to verify type consistency

**Estimated Effort**: 1-2 hours  
**Impact**: Low - Improves type safety  
**Risk**: None

---

## 🟢 Low Priority - Nice to Have

### 3. Extract Magic Numbers to Constants

**Files**: `tui.py`, `display.py`  
**Status**: ⏸️ Ready to start

**Tasks**:

- [ ] In `tui.py`: Extract `ITEM_NUMBER_WIDTH = 3`, `ITEM_NAME_WIDTH = 50`, etc.
- [ ] In `display.py`: Extract `PERCENTAGE_PRECISION = 1`
- [ ] Replace magic numbers with named constants
- [ ] Verify formatting still looks correct

**Estimated Effort**: 1 hour  
**Impact**: Low - Improves readability  
**Risk**: None

---

---

### 4. Organize Test Files in Root Directory

**Location**: Root directory  
**Status**: ⏸️ Ready to start

**Tasks**:

- [ ] Review `debug_keys_parsing.py` - move to exploration/ or delete
- [ ] Review `test_mixed_bundle.py` - move to tests/ or delete
- [ ] Review `test_keys_parsing.py` - move to tests/ or delete
- [ ] Review `test_keys_debug.py` - move to tests/ or delete
- [ ] Review `test_cli.py` - move to tests/ or delete
- [ ] Update .gitignore if needed

**Estimated Effort**: 30 minutes  
**Impact**: Low - Cleanup only  
**Risk**: None

---

### 5. Consider Splitting `BundleDetailsScreen` Class

**File**: `src/humblebundle_epub/tui.py`  
**Lines**: 169-405 (236 lines)  
**Status**: ⏸️ Optional - Only if class grows further

**Tasks**:

- [ ] Evaluate if split is necessary
- [ ] If yes, create `BundleDetailsLoader` for data loading
- [ ] If yes, create `BundleDetailsFormatter` for display formatting
- [ ] If yes, create `BundleDownloadHandler` for downloads
- [ ] Extensive testing required

**Estimated Effort**: 4-6 hours  
**Impact**: Low - Class is manageable as-is  
**Risk**: Medium - Major refactoring

---

## ✅ Completed

### Critical Antipatterns

- [x] Move `tui` import to top of `cli.py`
- [x] Move `traceback` import to top of `cli.py`
- [x] Move `re` import to top of `humble_wrapper.py`
- [x] Add `functools` import for decorator

### Unused Code

- [x] Remove `search_bundles()` function from `humble_wrapper.py`
- [x] Remove `download_bundle()` function from `humble_wrapper.py`
- [x] Remove `bundle_cache` variable from `tui.py`

### Code Quality

- [x] Create `handle_humble_cli_errors()` decorator
- [x] Apply decorator to `status()` command
- [x] Create `_create_file_id()` helper function
- [x] Replace duplicated file ID logic (2 instances)
- [x] Add `-> None` return type to `_ensure_initialized()`
- [x] Add `-> None` return type to `cycle_format()`
- [x] Fix all ruff linting issues in src/ and tests/ (10 issues resolved)

### Testing Infrastructure

- [x] Create `tests/` directory
- [x] Install pytest and pytest-cov
- [x] Create `tests/conftest.py`
- [x] Create `tests/__init__.py`
- [x] Create `tests/test_humble_wrapper.py` (20 tests)
- [x] Create `tests/test_epub_manager.py` (20 tests)
- [x] Achieve 72% coverage on complex methods
- [x] Verify all 40 tests passing
- [x] Install pytest-asyncio for async test support
- [x] Create `tests/test_tui.py` (21 tests)
- [x] Add TUI widget tests (BundleItem, ItemFormatRow)
- [x] Add TUI screen tests (BundleListScreen, BundleDetailsScreen)
- [x] Add TUI integration tests using Textual Pilot
- [x] Achieve 72% coverage on TUI module
- [x] Configure asyncio_mode in pyproject.toml
- [x] Overall: 61 tests passing, 55% total coverage
- [x] Create `tests/test_tracker.py` (12 tests)
- [x] Achieve 100% coverage on tracker module
- [x] Overall: 73 tests passing, 57% total coverage
- [x] Fix TypeError in display_bundle_status with None values
- [x] Create `tests/test_display.py` (4 tests)
- [x] Refactor test suites with fixtures and parametrization
- [x] Reduce test duplication: 77→67 test functions, 77→81 test cases
- [x] Extract temp_tracker fixture in test_tracker.py
- [x] Parametrize test_display.py (4 functions → 1 function, 4 cases)
- [x] Parametrize test_epub_manager.py (20 functions → 13 functions, 24 cases)
- [x] Overall: 81 tests passing, 62% total coverage

### Bug Fixes

- [x] Fix `status` command hanging (was calling get_bundle_details on all bundles)
- [x] Add `get_tracked_bundles()` method to tracker
- [x] Make `get_bundle_stats()` flexible with optional total_files parameter
- [x] Install pytest-asyncio for async test support
- [x] Create `tests/test_tui.py` (21 tests)
- [x] Add TUI widget tests (BundleItem, ItemFormatRow)
- [x] Add TUI screen tests (BundleListScreen, BundleDetailsScreen)
- [x] Add TUI integration tests with Pilot
- [x] Achieve 72% coverage on TUI module
- [x] Configure asyncio_mode in pyproject.toml

### Documentation

- [x] Create `CODE_REVIEW.md`
- [x] Update `REFACTORING_SUMMARY.md`
- [x] Create `PROGRESS_REPORT.md`
- [x] Create this `TODO.md`

### Complex Method Refactoring

- [x] Extract `_parse_bundle_name()` from `parse_bundle_details()` (11 lines)
- [x] Extract `_parse_metadata_field()` from `parse_bundle_details()` (14 lines)
- [x] Extract `_parse_items_table()` from `parse_bundle_details()` (51 lines)
- [x] Extract `_parse_keys_table()` from `parse_bundle_details()` (58 lines)
- [x] Refactor `parse_bundle_details()` to use helper functions (reduced from 155 lines to 19 lines)
- [x] Verify all 40 tests still pass (100% pass rate)
- [x] Maintain 71% coverage on `humble_wrapper.py`

---

## Future Considerations

### Not Currently Planned

- Add integration tests for CLI commands (would require mocking humble-cli)
- Add UI tests for TUI (would require Textual testing framework)
- Add performance benchmarks
- Add pre-commit hooks
- Set up CI/CD pipeline
- Add static type checking with mypy in CI

---

## Priority Legend

- 🔴 **High Priority**: Should be done soon, unblocks other work or high impact
- 🟡 **Medium Priority**: Important but can wait, moderate impact
- 🟢 **Low Priority**: Nice to have, low impact or optional

## Status Legend

- ⏸️ **Ready to start**: No blockers, can begin immediately
- 🔄 **In Progress**: Currently being worked on
- ✅ **Completed**: Done and verified
- ⛔ **Blocked**: Cannot proceed until blocker is resolved

---

## How to Use This TODO List

1. **Start with High Priority items** - These have the most impact
2. **Check Status before starting** - Ensure no blockers
3. **Update Status when you begin** - Change ⏸️ to 🔄
4. **Mark completed items** - Change 🔄 to ✅ and move to "Completed" section
5. **Add new items as needed** - Insert in appropriate priority section
6. **Review weekly** - Adjust priorities based on progress

---

## Quick Reference

**Next Actionable Task**: Complete return type hints (#2) - _Ready to start_  
**Alternative Next Task**: Extract magic numbers (#3) - _Ready to start_  
**Estimated Time to Clear Medium Priority**: ~1-2 hours  
**Total Remaining Effort**: ~3-6 hours  
**Test Count**: 81 tests passing (100% pass rate)  
**Overall Coverage**: 62% (up from 0%)
