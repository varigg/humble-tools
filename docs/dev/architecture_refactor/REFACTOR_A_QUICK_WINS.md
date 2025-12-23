# Refactor Phase A: Quick Wins

**Estimated Duration:** 1-2 days  
**Difficulty:** Low to Medium  
**Impact:** High (improves code consistency and quality immediately)

---

## Overview

This phase focuses on low-effort, high-impact improvements that can be completed quickly. These changes improve code quality, consistency, and tooling setup without requiring significant architectural changes.

---

## Task A.1: Fix Type Hint Inconsistencies

**Priority:** High  
**Estimated Time:** 1 hour  
**Files to Modify:**

- [src/humble_tools/sync/app.py](../../../src/humble_tools/sync/app.py)
- [src/humble_tools/core/humble_wrapper.py](../../../src/humble_tools/core/humble_wrapper.py)
- Various other files with missing or incorrect type hints

### Tasks

- [ ] **A.1.1** Add proper `typing` imports where missing

  ```python
  from typing import Any, Callable, Optional, TypeVar
  ```

- [ ] **A.1.2** Fix `_safe_query_widget` type hints in `app.py`

  ```python
  T = TypeVar('T')

  def _safe_query_widget(
      self,
      widget_id: str,
      widget_type: type[T],
      default_action: Optional[Callable[[], None]] = None,
  ) -> Optional[T]:
  ```

- [ ] **A.1.3** Add return type hints to all functions missing them

  - Search for functions without `->` return type
  - Add appropriate return types

- [ ] **A.1.4** Replace `Optional[x]` with `x | None` for Python 3.10+ style (if using 3.10+)

- [ ] **A.1.5** Run `ruff check --select ANN` to find missing annotations

### Validation

```bash
uv run ruff check --select ANN
uv run ty src/humble_tools  # If ty configured
```

---

## Task A.2: Add Ruff to Pre-commit Hooks

**Priority:** High  
**Estimated Time:** 30 minutes  
**Files to Create/Modify:**

- `.pre-commit-config.yaml`
- `pyproject.toml` (add ruff configuration)

### Tasks

- [ ] **A.2.1** Create `.pre-commit-config.yaml` if it doesn't exist

  ```yaml
  repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.12.3
      hooks:
        - id: ruff-check
          args: [--fix]
        - id: ruff-format
    - repo: https://github.com/gitleaks/gitleaks
      rev: v8.27.2
      hooks:
        - id: gitleaks
  ```

- [ ] **A.2.2** Add ruff configuration to `pyproject.toml`

  ```toml
  [tool.ruff]
  line-length = 100
  target-version = "py38"

  [tool.ruff.lint]
  select = [
      "E",  # pycodestyle errors
      "W",  # pycodestyle warnings
      "F",  # pyflakes
      "I",  # isort
      "B",  # flake8-bugbear
      "C4", # flake8-comprehensions
      "UP", # pyupgrade
  ]
  ignore = [
      "E501", # line too long (handled by formatter)
  ]

  [tool.ruff.format]
  quote-style = "double"
  indent-style = "space"
  ```

- [ ] **A.2.3** Install pre-commit

  ```bash
  uv tool install pre-commit
  pre-commit install
  ```

- [ ] **A.2.4** Run pre-commit on all files

  ```bash
  pre-commit run --all-files
  ```

- [ ] **A.2.5** Commit any formatting changes

### Validation

```bash
# Make a change and try to commit
git add .
git commit -m "test pre-commit"
# Should run ruff automatically
```

---

## Task A.3: Remove or Integrate Unused Validation Functions

**Priority:** Medium  
**Estimated Time:** 30 minutes  
**Files to Modify:**

- [src/humble_tools/core/validation.py](../../../src/humble_tools/core/validation.py)
- [src/humble_tools/core/download_manager.py](../../../src/humble_tools/core/download_manager.py)
- [tests/unit/test_validation.py](../../../tests/unit/test_validation.py)

### Tasks

- [ ] **A.3.1** Check if `check_disk_space()` is used anywhere

  ```bash
  grep -r "check_disk_space" src/
  ```

- [ ] **A.3.2** Check if `validate_output_directory()` is used anywhere

  ```bash
  grep -r "validate_output_directory" src/
  ```

- [ ] **A.3.3** **Option 1: Integrate into download flow** (Recommended)

  - Add validation to `download_manager.py`:

  ```python
  def download_item(
      self, bundle_key: str, item_number: int, format_name: str, output_dir: Path
  ) -> bool:
      """Download a specific format of an item and track it."""
      output_dir = Path(output_dir)

      # Validate output directory
      validate_output_directory(output_dir)

      # Continue with download...
  ```

- [ ] **A.3.4** **Option 2: Remove if truly unused** (Only if not planning to use)

  - Delete unused functions from `validation.py`
  - Remove corresponding tests
  - Update imports

- [ ] **A.3.5** Document decision in commit message

### Validation

```bash
uv run pytest tests/unit/test_validation.py
uv run pytest  # Run all tests
```

---

## Task A.4: Standardize Widget ID Usage

**Priority:** Low  
**Estimated Time:** 30 minutes  
**Files to Modify:**

- [src/humble_tools/sync/constants.py](../../../src/humble_tools/sync/constants.py)
- [src/humble_tools/sync/app.py](../../../src/humble_tools/sync/app.py)

### Tasks

- [ ] **A.4.1** Update `WidgetIds` class to include `#` prefix in constants

  ```python
  class WidgetIds:
      """Widget selector IDs used throughout the application."""

      # Bundle List Screen
      BUNDLE_LIST = "#bundle-list"
      STATUS_TEXT = "#status-text"
      SCREEN_HEADER = "#screen-header"

      # Bundle Details Screen
      BUNDLE_HEADER = "#bundle-header"
      BUNDLE_METADATA = "#bundle-metadata"
      ITEMS_LIST = "#items-list"
      DETAILS_STATUS = "#details-status"
      NOTIFICATION_AREA = "#notification-area"
  ```

- [ ] **A.4.2** Update all usages in `app.py` to use constants directly

  ```python
  # Before:
  self.query_one(f"#{WidgetIds.BUNDLE_LIST}", ListView)

  # After:
  self.query_one(WidgetIds.BUNDLE_LIST, ListView)
  ```

- [ ] **A.4.3** Search and replace all occurrences

  ```bash
  # Search for patterns like f"#{WidgetIds.
  grep -n 'f"#{WidgetIds' src/humble_tools/sync/app.py
  ```

- [ ] **A.4.4** Update `compose()` methods to use constants without quotes

  ```python
  # Before:
  yield Static("", id=WidgetIds.BUNDLE_HEADER)

  # After (if WidgetIds includes #, strip it):
  yield Static("", id=WidgetIds.BUNDLE_HEADER.lstrip("#"))
  ```

### Validation

```bash
uv run pytest tests/integration/
# Ensure UI tests still pass
```

---

## Task A.5: Extract Common Formatting Utilities

**Priority:** High  
**Estimated Time:** 2 hours  
**Files to Create:**

- [src/humble_tools/core/format_utils.py](../../../src/humble_tools/core/format_utils.py)

**Files to Modify:**

- [src/humble_tools/core/display.py](../../../src/humble_tools/core/display.py)
- [src/humble_tools/sync/app.py](../../../src/humble_tools/sync/app.py)

### Tasks

- [ ] **A.5.1** Create `src/humble_tools/core/format_utils.py`

  ```python
  """Common formatting utilities shared across CLI and TUI."""

  from typing import Optional


  class FormatUtils:
      """Shared formatting utilities."""

      @staticmethod
      def format_file_size(size_bytes: int) -> str:
          """Convert bytes to human-readable size.

          Args:
              size_bytes: Size in bytes

          Returns:
              Human-readable size string (e.g., "1.5 GB", "250 MB")
          """
          for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
              if size_bytes < 1024.0:
                  return f"{size_bytes:.1f} {unit}"
              size_bytes /= 1024.0
          return f"{size_bytes:.1f} PB"

      @staticmethod
      def format_download_progress(
          downloaded: int,
          total: Optional[int]
      ) -> str:
          """Format download progress as a percentage or status.

          Args:
              downloaded: Number of items downloaded
              total: Total number of items, or None if unknown

          Returns:
              Formatted progress string (e.g., "75.0%", "5/?")
          """
          if total is None:
              return f"{downloaded}/?"
          if total == 0:
              return "0%"
          percentage = (downloaded / total) * 100
          return f"{percentage:.1f}%"

      @staticmethod
      def format_bundle_stats(
          downloaded: int,
          total: Optional[int]
      ) -> str:
          """Format bundle statistics string.

          Args:
              downloaded: Number downloaded
              total: Total number or None

          Returns:
              Formatted string (e.g., "5/10", "5/?")
          """
          if total is None:
              return f"{downloaded}/?"
          return f"{downloaded}/{total}"

      @staticmethod
      def truncate_string(text: str, max_length: int) -> str:
          """Truncate string to max length with ellipsis.

          Args:
              text: String to truncate
              max_length: Maximum length (including ellipsis)

          Returns:
              Truncated string
          """
          if len(text) <= max_length:
              return text
          return text[:max_length-3] + "..."
  ```

- [ ] **A.5.2** Add tests for `format_utils.py`

  - Create `tests/unit/test_format_utils.py`
  - Test each formatting function

- [ ] **A.5.3** Update `display.py` to use `FormatUtils`

  - Import and use formatting functions where applicable
  - Remove any duplicate formatting logic

- [ ] **A.5.4** Update `app.py` to use `FormatUtils` where applicable

### Validation

```bash
uv run pytest tests/unit/test_format_utils.py
uv run pytest  # Run all tests
```

---

## Task A.6: Move CLI-Specific Display Code to Track Directory

**Priority:** Medium  
**Estimated Time:** 1 hour  
**Files to Create:**

- [src/humble_tools/track/display.py](../../../src/humble_tools/track/display.py)

**Files to Modify:**

- [src/humble_tools/core/display.py](../../../src/humble_tools/core/display.py) (extract CLI code)
- [src/humble_tools/track/commands.py](../../../src/humble_tools/track/commands.py) (update imports)

### Tasks

- [ ] **A.6.1** Analyze `core/display.py` to identify CLI-specific functions

  - `display_bundles()` - CLI specific
  - `display_tracked_bundles_summary()` - CLI specific
  - `display_bundle_status()` - CLI specific
  - `display_bundle_items()` - CLI specific
  - Console print helpers - CLI specific

- [ ] **A.6.2** Create `src/humble_tools/track/display.py`

  ```python
  """Rich console output formatting for CLI commands."""

  from typing import Dict, List

  from rich.console import Console
  from rich.panel import Panel
  from rich.table import Table

  from humble_tools.core.format_utils import FormatUtils

  console = Console()


  def display_bundles(bundles: List[Dict], with_stats: bool = False):
      """Display bundles in a formatted table."""
      # Move implementation from core/display.py
      ...

  # ... other CLI-specific functions
  ```

- [ ] **A.6.3** Keep only shared/generic functions in `core/display.py`

  - Generic print helpers like `print_error()`, `print_success()`, etc.
  - Progress bar utilities if shared between CLI and TUI

- [ ] **A.6.4** Update imports in `track/commands.py`

  ```python
  # Before:
  from humble_tools.core.display import display_bundle_status

  # After:
  from humble_tools.track.display import display_bundle_status
  ```

- [ ] **A.6.5** Update any tests that import from `core.display`

### Validation

```bash
uv run pytest tests/unit/test_display.py
uv run pytest  # Run all tests
humble-track status  # Test CLI command
```

---

## Completion Checklist

- [ ] All tasks in A.1 completed and validated
- [ ] All tasks in A.2 completed and validated
- [ ] All tasks in A.3 completed and validated
- [ ] All tasks in A.4 completed and validated
- [ ] All tasks in A.5 completed and validated
- [ ] All tasks in A.6 completed and validated
- [ ] All tests passing: `uv run pytest`
- [ ] Pre-commit hooks working correctly
- [ ] Code formatted with ruff: `uv run ruff format .`
- [ ] Linting passes: `uv run ruff check .`
- [ ] Documentation updated if needed
- [ ] Commit with message: "refactor: Phase A Quick Wins - code quality improvements"

---

## Notes

- These tasks can be done in any order, though A.2 (ruff setup) should be done early
- Tasks A.5 and A.6 work together to improve display code organization
- Consider pairing A.1 with A.2 so type checking can be validated automatically
- If any task takes longer than estimated, document the reason and adjust future estimates

---

## Next Steps

After completing this phase, proceed to [REFACTOR_B_STRUCTURAL.md](REFACTOR_B_STRUCTURAL.md) for structural improvements.
