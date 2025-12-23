# Project Restructuring Analysis - What Went Wrong

## Summary

The project restructuring from `humblebundle_epub` to `humble_tools` with modular organization was mostly successful, but test execution failed due to corrupted test files from improper use of `sed` commands.

## What Was Successfully Completed

### 1. Package Structure ✅

- Renamed `src/humblebundle_epub/` → `src/humble_tools/`
- Created modular subdirectories: `core/`, `sync/`, `track/`
- Moved files to appropriate modules:
  - `core/`: `humble_wrapper.py`, `tracker.py`, `display.py`, `download_manager.py` (renamed from `epub_manager.py`)
  - `sync/`: `app.py` (renamed from `tui.py`) with `__init__.py` entry point
  - `track/`: `commands.py` (renamed from `cli.py`) with `__init__.py` entry point

### 2. Import Updates ✅

- Fixed imports in all source files to use new `humble_tools.core.*` paths
- Updated class name: `EPUBManager` → `EpubManager`
- Created proper `__init__.py` files for each module
- Removed non-existent `HumbleBundleAPI` class from core `__init__.py`

### 3. Configuration Updates ✅

- Updated `pyproject.toml`:
  - Package name: `humblebundle-epub` → `humble-tools`
  - Entry points:
    - `humble-sync = "humble_tools.sync:main"`
    - `humble-track = "humble_tools.track.commands:main"`

### 4. Test Organization ✅

- Created test subdirectories: `test_core/`, `test_sync/`, `test_track/`
- Moved test files to appropriate locations
- Renamed `test_epub_manager.py` → `test_download_manager.py`
- Renamed `test_tui.py` → `test_app.py`
- Updated test imports to use new `humble_tools.*` paths
- Correctly avoided creating `__init__.py` in test directories (modern pytest doesn't need them)

## What Went Wrong

### Critical Failure: sed Command Corruption 🚨

**Problem**: Used `sed` commands to batch-update `@patch` decorators in test files, which corrupted the files with mixed quotes.

**What happened**:

1. First sed: `s/@patch.*humblebundle_epub\.epub_manager\./@patch("humble_tools.core.download_manager./g`

   - Replaced opening with `"` but left existing closing quotes unchanged
   - Result: `@patch("humble_tools.core.download_manager.get_bundles')` ← mixed quotes!

2. Second sed tried to fix: `s|')$|")|g`
   - Blindly replaced ALL `')` at end of lines
   - Corrupted legitimate code: `'bundle')` → `'bundle")`
   - Created syntax errors throughout the file

**Files affected**:

- `tests/test_core/test_download_manager.py` - severely damaged
- `tests/test_sync/test_app.py` - moderately damaged

**Why sed failed**:

- Regex patterns were too broad and context-insensitive
- Multiple passes with different quote styles created inconsistencies
- No validation after each change
- sed doesn't understand Python syntax, so it matched unintended lines

### Secondary Issues

1. **No backup strategy**: Files weren't tracked in git, so `git checkout` couldn't restore them
2. **Incremental damage**: Each sed attempt made things worse instead of reverting
3. **Late detection**: Syntax errors only caught when pytest tried to parse the files

## Correct Approach (Not Taken)

### Option 1: Read, Replace, Write in Python

```python
import re

with open('file.py', 'r') as f:
    content = f.read()

# Precise regex with full match
content = re.sub(
    r"@patch\(['\"]humblebundle_epub\.epub_manager\.([a-z_]+)['\"]\)",
    r"@patch('humble_tools.core.download_manager.\1')",
    content
)

with open('file.py', 'w') as f:
    f.write(content)
```

### Option 2: Use replace_string_in_file Tool

```python
# Replace each decorator individually with full context
replace_string_in_file(
    filePath="tests/test_core/test_download_manager.py",
    oldString="""    @patch('humblebundle_epub.epub_manager.get_bundle_details')
    @patch('humblebundle_epub.epub_manager.parse_bundle_details')
    def test_get_bundle_items_adds_download_status(""",
    newString="""    @patch('humble_tools.core.download_manager.get_bundle_details')
    @patch('humble_tools.core.download_manager.parse_bundle_details')
    def test_get_bundle_items_adds_download_status("""
)
```

### Option 3: Multi-file replace with validation

```python
# Use multi_replace_string_in_file with precise context
# Validate syntax after each file
# pytest --collect-only to check for import errors
```

## Current State

### What Works

- Package structure is correct
- All source file imports are updated
- Entry points are configured
- Test file organization is correct
- Test imports are updated

### What's Broken

- `tests/test_core/test_download_manager.py` has syntax errors (mixed quotes)
- `tests/test_sync/test_app.py` may have similar issues
- Cannot run test suite until files are manually repaired

### Recovery Strategy

1. **Manual inspection**: Read test files to identify all corrupted strings
2. **Targeted fixes**: Use `replace_string_in_file` with exact context for each error
3. **Validation**: Run `python -m py_compile tests/test_core/test_download_manager.py` after each fix
4. **Final test**: Run `uv run pytest tests/ --collect-only` to verify all files parse
5. **Full run**: Execute complete test suite

## Lessons Learned

1. **Never use sed for Python refactoring** - It doesn't understand syntax
2. **Always validate immediately** - Check syntax after each batch change
3. **Use version control** - Even for experimental work, commit before major changes
4. **Prefer precise tools** - `replace_string_in_file` with context > blind regex
5. **Test incrementally** - Run tests after each logical change, not at the end
6. **Python for Python** - Use Python scripts for Python code manipulation

## Estimated Recovery Time

- **Manual fix**: 15-20 minutes to repair all corrupted strings
- **Automated fix**: 5 minutes with precise `replace_string_in_file` operations
- **Complete verification**: 5 minutes to run full test suite

## Overall Assessment

The restructuring plan was sound and 90% executed correctly. The failure was entirely in the final step of updating test file decorators, caused by inappropriate tool choice (sed vs. context-aware replace). The underlying code changes are all valid - we just corrupted the test files with a bad refactoring tool.

**Status**: Recoverable with targeted fixes. No need to restart the restructuring.
