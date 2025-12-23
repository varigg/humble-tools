# Code Review - Python Idioms and Refactoring Opportunities

## Summary

Overall, the codebase is well-structured with good separation of concerns. However, there are several antipatterns, complexity issues, and opportunities for refactoring.

## Critical Issues

### 1. ❌ **ANTIPATTERN: Import Inside Function** - `cli.py`

**Location**: `cli.py:103`

```python
def tui(output):
    """Launch interactive TUI for browsing and downloading bundles."""
    from .tui import run_tui  # ❌ Import not at top of file
```

**Problem**: Import is inside function, violating PEP 8. This is typically done to avoid circular imports, but there's no circular dependency here.

**Fix**: Move to top-level imports.

---

### 2. ❌ **ANTIPATTERN: Import Inside Function** - `cli.py`

**Location**: `cli.py:126`

```python
except Exception as e:
    print_error(f"Error running TUI: {e}")
    import traceback  # ❌ Import not at top of file
    traceback.print_exc()
```

**Problem**: `traceback` import should be at module level.

**Fix**: Move to top-level imports.

---

### 3. ❌ **ANTIPATTERN: Import Inside Function** - `humble_wrapper.py`

**Location**: `humble_wrapper.py:116`

```python
def parse_bundle_details(details_output: str) -> Dict:
    """Parse bundle details output into structured data."""
    import re  # ❌ Import not at top of file
```

**Problem**: `re` is used throughout the module but only imported inside one function.

**Fix**: Move to top-level imports.

---

### 4. ⚠️ **UNUSED CODE: Functions Never Called**

**Location**: `humble_wrapper.py`

These functions are defined but never used after CLI refactoring:

```python
# Line 253: Never called
def search_bundles(keywords: List[str], mode: str = "any") -> List[str]:
    """Search for bundles matching keywords."""
    # ... implementation ...

# Line 276: Never called (CLI download command removed)
def download_bundle(
    bundle_key: str,
    output_dir: str,
    formats: Optional[List[str]] = None,
    item_numbers: Optional[str] = None,
    dry_run: bool = False
) -> bool:
    """Download files from a bundle."""
    # ... implementation ...
```

**Fix**: Remove these functions or mark them for potential future use.

---

## Complexity Issues

### 5. 🔴 **COMPLEX METHOD: parse_bundle_details()** - `humble_wrapper.py`

**Location**: `humble_wrapper.py:95-249` (155 lines!)

**Complexity Score**: Very High

- **Lines**: 155 lines
- **Cyclomatic Complexity**: ~15
- **Multiple responsibilities**: Parsing headers, items table, keys table
- **Nested loops and conditionals**: 3-4 levels deep

**Problems**:

```python
def parse_bundle_details(details_output: str) -> Dict:
    # 1. Parse header (20 lines)
    # 2. Find table start (10 lines)
    # 3. Parse items table (30 lines)
    # 4. Parse keys section (50 lines)
    # Total: 155 lines of complex parsing logic
```

**Recommended Refactoring**:

```python
def parse_bundle_details(details_output: str) -> Dict:
    """Parse bundle details - delegating to specialized parsers."""
    lines = details_output.strip().split('\n')

    return {
        'name': _parse_bundle_name(lines),
        'purchased': _parse_metadata_field(lines, 'Purchased'),
        'amount': _parse_metadata_field(lines, 'Amount spent'),
        'total_size': _parse_metadata_field(lines, 'Total size'),
        'items': _parse_items_table(lines),
        'keys': _parse_keys_table(lines)
    }

def _parse_bundle_name(lines: List[str]) -> str:
    """Extract bundle name from first non-empty line."""
    return lines[0].strip() if lines else ''

def _parse_metadata_field(lines: List[str], field_name: str) -> str:
    """Extract a metadata field value."""
    for line in lines:
        if field_name in line:
            match = re.search(rf'{field_name}\s*:\s*(.+)', line)
            if match:
                return match.group(1).strip()
    return ''

def _parse_items_table(lines: List[str]) -> List[Dict]:
    """Parse the items table section."""
    # ... focused parsing logic ...

def _parse_keys_table(lines: List[str]) -> List[Dict]:
    """Parse the keys table section."""
    # ... focused parsing logic ...
```

**Benefits**:

- Each function has a single responsibility
- Easier to test individually
- Easier to debug
- Better code reuse

---

### 6. 🔴 **COMPLEX METHOD: load_details()** - `tui.py`

**Location**: `tui.py:225-325` (100 lines)

**Complexity Score**: High

- **Lines**: 100 lines
- **Multiple responsibilities**: Loading data, updating UI, handling empty states, formatting displays
- **Nested conditionals**: 3-4 levels deep

**Problems**:

```python
@work(exclusive=True)
async def load_details(self) -> None:
    """Load bundle details in background."""
    try:
        # Get data
        self.bundle_data = self.epub_manager.get_bundle_items(self.bundle_key)

        # Update metadata (10 lines)
        # ...

        # Check if no items (30 lines of conditional logic)
        if not self.bundle_data['items']:
            if self.bundle_data.get('keys'):
                # Show keys (20 lines)
            else:
                # Show empty state (5 lines)
            return

        # Add items to list (40 lines)
        # ...

    except HumbleCLIError as e:
        # Error handling (5 lines)
```

**Recommended Refactoring**:

```python
@work(exclusive=True)
async def load_details(self) -> None:
    """Load bundle details in background."""
    try:
        self.bundle_data = self.epub_manager.get_bundle_items(self.bundle_key)
        self._update_metadata_display()

        if not self.bundle_data['items']:
            self._display_keys_or_empty_state()
        else:
            self._display_items_list()

    except HumbleCLIError as e:
        self._show_error(str(e))

def _update_metadata_display(self) -> None:
    """Update the metadata section of the UI."""
    # ... focused display logic ...

def _display_keys_or_empty_state(self) -> None:
    """Handle bundles with no downloadable items."""
    if self.bundle_data.get('keys'):
        self._display_keys_table()
    else:
        self._display_empty_bundle()

def _display_keys_table(self) -> None:
    """Display game keys in a formatted table."""
    # ... focused display logic ...

def _display_items_list(self) -> None:
    """Display downloadable items in a list."""
    # ... focused display logic ...
```

---

### 7. 🟡 **COMPLEX METHOD: BundleDetailsScreen class** - `tui.py`

**Location**: `tui.py:169-405` (236 lines)

**Problem**: This class is doing too much:

- Managing UI state
- Loading data
- Formatting displays
- Handling downloads
- Managing navigation

**Recommendation**: Consider splitting into:

- `BundleDetailsScreen` - UI state and navigation
- `BundleDetailsLoader` - Data loading logic
- `BundleDetailsFormatter` - Display formatting
- `BundleDownloadHandler` - Download operations

---

## Code Duplication

### 8. 🟡 **DUPLICATED: Exception Handling Pattern**

**Locations**: Multiple files

```python
# cli.py:80
except HumbleCLIError as e:
    print_error(str(e))
    sys.exit(1)

# cli.py:54-56 (same pattern)
except HumbleCLIError as e:
    print_error(str(e))
    sys.exit(1)
```

**Recommendation**: Create a decorator or context manager:

```python
def handle_humble_cli_errors(func):
    """Decorator to handle HumbleCLIError consistently."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HumbleCLIError as e:
            print_error(str(e))
            sys.exit(1)
    return wrapper

# Usage:
@main.command()
@click.pass_context
@handle_humble_cli_errors
def status(ctx, bundle_key):
    """Show download progress for bundles."""
    _ensure_initialized(ctx)
    # ... rest of implementation without try/except ...
```

---

### 9. 🟡 **DUPLICATED: File ID Generation**

**Locations**: `epub_manager.py`

```python
# Line 157
file_id = f"{bundle_key}_{item['number']}_{fmt.lower()}"

# Line 183
file_id = f"{bundle_key}_{item_number}_{format_name.lower()}"
```

**Recommendation**: Extract to a helper function:

```python
def _create_file_id(bundle_key: str, item_number: int, format_name: str) -> str:
    """Create a unique identifier for a bundle item format.

    Args:
        bundle_key: Bundle identifier
        item_number: Item number within bundle
        format_name: File format (e.g., 'epub', 'pdf')

    Returns:
        Unique file identifier string
    """
    return f"{bundle_key}_{item_number}_{format_name.lower()}"
```

---

### 10. 🟡 **DUPLICATED: Download Status Checking**

**Locations**: `tui.py`

```python
# Lines 341-343 (download_item method)
status = self.query_one("#details-status", Static)
status.update(f"[cyan]Downloading item #{selected.item_number}...")

# Lines 361-363 (on_list_view_selected method)
status = self.query_one("#details-status", Static)
status.update(f"[cyan]Downloading item #{selected.item_number}...")
```

**Recommendation**: Extract to helper method:

```python
def _update_status(self, message: str, style: str = "white") -> None:
    """Update the status line with a message."""
    status = self.query_one("#details-status", Static)
    status.update(f"[{style}]{message}[/{style}]")

# Usage:
self._update_status(
    f"Downloading item #{selected.item_number} ({selected.selected_format})...",
    "cyan"
)
```

---

## Minor Issues

### 11. 🟢 **UNUSED IMPORT: Console** - `cli.py`

**Location**: `cli.py:9`

The `console` is imported but never used directly in `cli.py` (only passed through to display functions).

**Fix**: Consider if it's needed at all.

---

### 12. 🟢 **UNUSED VARIABLE: `bundle_cache`** - `tui.py`

**Location**: `tui.py:446`

```python
def __init__(self, output_dir: Optional[Path] = None):
    # ...
    self.bundle_cache = {}  # Never used!
```

**Fix**: Remove or implement caching if needed.

---

### 13. 🟢 **MAGIC NUMBERS** - Multiple files

**Locations**: Various

```python
# tui.py:68
text = f"{self.item_number:3d} | {self.item_name[:50]:50s} | {formats_str:30s} | {self.item_size:>10s}"
#                          ^^^          ^^^            ^^^             ^^^
# What do these numbers mean?

# display.py:133
progress_text.append(f"({percentage:.1f}%)", style="cyan")
#                                    ^^^
# Why .1f precision?
```

**Recommendation**: Extract to named constants:

```python
# tui.py
ITEM_NUMBER_WIDTH = 3
ITEM_NAME_WIDTH = 50
FORMATS_WIDTH = 30
SIZE_WIDTH = 10

# display.py
PERCENTAGE_PRECISION = 1
```

---

### 14. 🟢 **INCONSISTENT STRING FORMATTING**

**Locations**: Various

Mix of f-strings, .format(), and % formatting:

```python
# cli.py uses f-strings (good)
print_error(f"humble-cli is not installed or not in PATH")

# humble_wrapper.py uses f-strings (good)
raise HumbleCLIError(f"Failed to list bundles: {e.stderr}")

# display.py uses f-strings (good)
f"{downloaded}/{total} files downloaded "
```

**Status**: ✅ Good - already consistent with f-strings

---

### 15. 🟢 **MISSING RETURN TYPE HINTS** - Various functions

**Examples**:

```python
# humble_wrapper.py:15
def check_humble_cli() -> bool:  # ✅ Has return type

# cli.py:37
def _ensure_initialized(ctx):  # ❌ Missing return type (should be -> None)

# tui.py:74
def cycle_format(self):  # ❌ Missing return type (should be -> None)
```

**Recommendation**: Add `-> None` to functions that don't return values.

---

## Recommendations Priority

### 🔴 High Priority (Do First)

1. **Fix import antipatterns** - Move all imports to top of file
2. **Remove unused functions** - `search_bundles()`, `download_bundle()` in `humble_wrapper.py`
3. **Refactor `parse_bundle_details()`** - Split into smaller functions

### 🟡 Medium Priority (Do Next)

4. **Refactor `load_details()`** - Extract display logic into helper methods
5. **Extract duplicated code** - Error handling decorator, file ID generation
6. **Add return type hints** - Complete type annotations

### 🟢 Low Priority (Nice to Have)

7. **Remove unused variables** - `bundle_cache` in TUI
8. **Extract magic numbers** - Named constants for display widths
9. **Consider splitting BundleDetailsScreen** - If class grows further

---

## Unused Test Files (Consider Removing)

These test files in the root directory should be moved to a `tests/` directory or removed:

```
/home/varigg/projects/python/humblebundle/
├── debug_keys_parsing.py      # Debug script - remove or move to exploration/
├── test_mixed_bundle.py       # Test script - move to tests/
├── test_keys_parsing.py       # Test script - move to tests/
├── test_keys_debug.py         # Test script - move to tests/
└── test_cli.py                # Test script - move to tests/
```

**Recommendation**: Create a `tests/` directory and organize test files properly.

---

## Summary Statistics

| Category              | Count  |
| --------------------- | ------ |
| Critical Antipatterns | 3      |
| Complex Methods       | 3      |
| Code Duplications     | 5      |
| Minor Issues          | 5      |
| Unused Code           | 3      |
| **Total Issues**      | **19** |

## Estimated Refactoring Effort

- **Critical fixes**: 2-3 hours
- **Complexity refactoring**: 4-6 hours
- **Duplication removal**: 1-2 hours
- **Minor fixes**: 1 hour
- **Total**: 8-12 hours
