# Refactor Phase B: Structural Improvements

**Estimated Duration:** 3-5 days  
**Difficulty:** Medium  
**Impact:** High (improves code maintainability and testability)

---

## Overview

This phase focuses on structural improvements that enhance code organization, reduce duplication, and improve maintainability. These changes require more significant refactoring but provide substantial benefits in code quality and testability.

---

## Task B.1: Extract BundleDetailsParser Class

**Priority:** High  
**Estimated Time:** 3-4 hours  
**Files to Create:**

- [src/humble_tools/core/parsers.py](../../../src/humble_tools/core/parsers.py)
- [tests/unit/test_parsers.py](../../../tests/unit/test_parsers.py)

**Files to Modify:**

- [src/humble_tools/core/humble_wrapper.py](../../../src/humble_tools/core/humble_wrapper.py)

### Tasks

- [ ] **B.1.1** Create `src/humble_tools/core/parsers.py` with parser class

  ```python
  """Parsers for humble-cli command output."""

  import re
  from typing import Dict, List


  class BundleDetailsParser:
      """Parse humble-cli details output into structured data."""

      def __init__(self, output: str):
          """Initialize parser with command output.

          Args:
              output: Raw output from humble-cli details command
          """
          self.output = output
          self.lines = output.strip().split("\n")

      def parse(self) -> Dict:
          """Parse complete bundle details.

          Returns:
              Dictionary with bundle_name, purchased, amount, total_size, items, keys
          """
          return {
              "bundle_name": self._parse_name(),
              "purchased": self._parse_field("Purchased"),
              "amount": self._parse_field("Amount spent"),
              "total_size": self._parse_field("Total size"),
              "items": self._parse_items(),
              "keys": self._parse_keys(),
          }

      def _parse_name(self) -> str:
          """Extract bundle name from first line."""
          return self.lines[0].strip() if self.lines else ""

      def _parse_field(self, field_name: str) -> str:
          """Extract metadata field value.

          Args:
              field_name: Field name to search for (e.g., 'Purchased')

          Returns:
              Field value or empty string if not found
          """
          for line in self.lines:
              if field_name in line:
                  match = re.search(rf"{field_name}\s*:\s*(.+)", line)
                  if match:
                      return match.group(1).strip()
          return ""

      def _find_table_start(self, header_pattern: str) -> int:
          """Find the starting line index of a table.

          Args:
              header_pattern: Regex pattern to match table header

          Returns:
              Line index after the header separator, or -1 if not found
          """
          for i, line in enumerate(self.lines):
              if re.match(header_pattern, line):
                  return i + 2  # Skip header and separator line
          return -1

      def _parse_items(self) -> List[Dict]:
          """Parse items table from bundle details.

          Returns:
              List of items with number, name, formats, and size
          """
          items = []
          table_start = self._find_table_start(r"\s*#\s*\|\s*Sub-item")

          if table_start == -1:
              return items

          for line in self.lines[table_start:]:
              line = line.strip()
              if not line:
                  continue

              # Stop if we hit a section header
              if line.endswith(":"):
                  break

              item = self._parse_item_row(line)
              if item:
                  items.append(item)

          return items

      def _parse_item_row(self, line: str) -> Dict | None:
          """Parse a single item row.

          Args:
              line: Table row string

          Returns:
              Item dictionary or None if parsing fails
          """
          # Example: "  1 | Book Name | MOBI, EPUB |   3.47 MiB"
          match = re.match(
              r"\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(.+)",
              line
          )
          if not match:
              return None

          item_number = int(match.group(1))
          item_name = match.group(2).strip()
          formats_str = match.group(3).strip()
          size = match.group(4).strip()

          # Parse formats (comma-separated)
          formats = [fmt.strip().upper() for fmt in formats_str.split(",")]

          return {
              "number": item_number,
              "name": item_name,
              "formats": formats,
              "size": size,
          }

      def _parse_keys(self) -> List[Dict]:
          """Parse keys table from bundle details.

          Returns:
              List of keys with number, name, and redeemed status
          """
          keys = []

          # Find "Keys in this bundle:" line
          keys_section_start = -1
          for i, line in enumerate(self.lines):
              if "Keys in this bundle:" in line:
                  keys_section_start = i + 1
                  break

          if keys_section_start == -1:
              return keys

          # Find table header
          table_start = self._find_table_start_from_index(
              r"\s*#\s*\|\s*Key Name",
              keys_section_start
          )

          if table_start == -1:
              return keys

          for line in self.lines[table_start:]:
              line = line.strip()
              if not line:
                  continue

              key = self._parse_key_row(line)
              if key:
                  keys.append(key)

          return keys

      def _find_table_start_from_index(
          self,
          header_pattern: str,
          start_index: int
      ) -> int:
          """Find table start from a specific index.

          Args:
              header_pattern: Regex pattern to match
              start_index: Index to start searching from

          Returns:
              Line index after header separator, or -1 if not found
          """
          for i in range(start_index, len(self.lines)):
              if re.match(header_pattern, self.lines[i]):
                  return i + 2  # Skip header and separator
          return -1

      def _parse_key_row(self, line: str) -> Dict | None:
          """Parse a single key row.

          Args:
              line: Table row string

          Returns:
              Key dictionary or None if parsing fails
          """
          # Example: "  1 | Game Name | Yes |"
          match = re.match(
              r"\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(Yes|No)",
              line
          )
          if not match:
              return None

          return {
              "number": int(match.group(1)),
              "name": match.group(2).strip(),
              "redeemed": match.group(3).strip() == "Yes",
          }
  ```

- [ ] **B.1.2** Create comprehensive tests in `tests/unit/test_parsers.py`

  ```python
  """Tests for bundle details parser."""

  import pytest

  from humble_tools.core.parsers import BundleDetailsParser


  def test_parse_bundle_name():
      """Test parsing bundle name."""
      output = "Test Bundle\nPurchased: 2024-01-01\n"
      parser = BundleDetailsParser(output)
      assert parser._parse_name() == "Test Bundle"


  def test_parse_metadata_field():
      """Test parsing metadata fields."""
      output = """Bundle Name
      Purchased: 2024-01-01
      Amount spent: $15.00
      Total size: 150 MB
      """
      parser = BundleDetailsParser(output)
      assert parser._parse_field("Purchased") == "2024-01-01"
      assert parser._parse_field("Amount spent") == "$15.00"
      assert parser._parse_field("Total size") == "150 MB"


  def test_parse_items_table():
      """Test parsing items table."""
      output = """Bundle Name

      #  | Sub-item | Format | Total Size
      ---|----------|--------|------------
       1 | Book One | EPUB, PDF | 5 MB
       2 | Book Two | MOBI | 3 MB
      """
      parser = BundleDetailsParser(output)
      items = parser._parse_items()

      assert len(items) == 2
      assert items[0]["number"] == 1
      assert items[0]["name"] == "Book One"
      assert items[0]["formats"] == ["EPUB", "PDF"]
      assert items[0]["size"] == "5 MB"


  def test_parse_keys_table():
      """Test parsing keys table."""
      output = """Bundle Name

      Keys in this bundle:

      #  | Key Name | Redeemed
      ---|----------|----------
       1 | Game One | Yes
       2 | Game Two | No
      """
      parser = BundleDetailsParser(output)
      keys = parser._parse_keys()

      assert len(keys) == 2
      assert keys[0]["number"] == 1
      assert keys[0]["name"] == "Game One"
      assert keys[0]["redeemed"] is True
      assert keys[1]["redeemed"] is False


  def test_parse_complete_bundle():
      """Test parsing complete bundle details."""
      output = """Test Bundle
      Purchased: 2024-01-01
      Amount spent: $15.00
      Total size: 150 MB

      #  | Sub-item | Format | Total Size
      ---|----------|--------|------------
       1 | Book One | EPUB | 5 MB

      Keys in this bundle:

      #  | Key Name | Redeemed
      ---|----------|----------
       1 | Game One | No
      """
      parser = BundleDetailsParser(output)
      result = parser.parse()

      assert result["bundle_name"] == "Test Bundle"
      assert result["purchased"] == "2024-01-01"
      assert result["amount"] == "$15.00"
      assert result["total_size"] == "150 MB"
      assert len(result["items"]) == 1
      assert len(result["keys"]) == 1
  ```

- [ ] **B.1.3** Update `humble_wrapper.py` to use the parser

  ```python
  def parse_bundle_details(output: str) -> Dict:
      """Parse bundle details output into structured data.

      Args:
          output: Raw output from humble-cli details command

      Returns:
          Dictionary with parsed bundle information
      """
      parser = BundleDetailsParser(output)
      return parser.parse()
  ```

- [ ] **B.1.4** Remove old parsing functions from `humble_wrapper.py`

  - `_parse_bundle_name()`
  - `_parse_metadata_field()`
  - `_parse_items_table()`
  - `_parse_keys_table()`

- [ ] **B.1.5** Update imports and references throughout codebase

### Validation

```bash
uv run pytest tests/unit/test_parsers.py -v
uv run pytest tests/unit/test_humble_wrapper.py -v
uv run pytest  # Run all tests
```

---

## Task B.2: Add Database Connection Lifecycle Management

**Priority:** High  
**Estimated Time:** 1-2 hours  
**Files to Modify:**

- [src/humble_tools/core/tracker.py](../../../src/humble_tools/core/tracker.py)
- [src/humble_tools/track/commands.py](../../../src/humble_tools/track/commands.py)
- [tests/unit/test_tracker.py](../../../tests/unit/test_tracker.py)

### Tasks

- [ ] **B.2.1** Add context manager support to `DownloadTracker`

  ```python
  class DownloadTracker:
      """Track downloaded files in a database."""

      def __init__(self, db_connection: Optional[SQLiteConnection] = None):
          """Initialize the download tracker."""
          if db_connection is None:
              db_connection = create_default_connection()

          self._conn = db_connection
          self._owns_connection = db_connection is None

      def close(self) -> None:
          """Close database connection if owned by this tracker."""
          if self._owns_connection and self._conn:
              self._conn.close()
              self._conn = None

      def __enter__(self):
          """Enter context manager."""
          return self

      def __exit__(self, exc_type, exc_val, exc_tb):
          """Exit context manager and close connection."""
          self.close()
          return False
  ```

- [ ] **B.2.2** Update `DownloadManager` to properly manage tracker lifecycle

  ```python
  class DownloadManager:
      """Manage file discovery and downloads."""

      def __init__(self, tracker: Optional[DownloadTracker] = None):
          """Initialize download manager."""
          self.tracker = tracker or DownloadTracker()
          self._owns_tracker = tracker is None

      def close(self) -> None:
          """Close resources if owned."""
          if self._owns_tracker and self.tracker:
              self.tracker.close()

      def __enter__(self):
          return self

      def __exit__(self, exc_type, exc_val, exc_tb):
          self.close()
          return False
  ```

- [ ] **B.2.3** Update CLI commands to use context managers

  ```python
  @main.command()
  @click.pass_context
  def status(ctx, bundle_key):
      """Show download progress for bundles."""
      _ensure_initialized(ctx)

      with ctx.obj["download_manager"] as dm:
          # Use download manager
          stats = dm.get_bundle_stats(bundle_key)
          # ...
  ```

- [ ] **B.2.4** Update tests to use context managers

  ```python
  def test_tracker_lifecycle():
      """Test tracker properly closes connection."""
      with DownloadTracker() as tracker:
          tracker.mark_downloaded("url", "bundle", "file")
          assert tracker.is_downloaded("url")
      # Connection should be closed here
  ```

- [ ] **B.2.5** Add tests for ownership semantics
  ```python
  def test_tracker_does_not_close_external_connection():
      """Test tracker doesn't close externally provided connection."""
      conn = SQLiteConnection(":memory:")
      with DownloadTracker(db_connection=conn) as tracker:
          tracker.mark_downloaded("url", "bundle", "file")
      # Connection should still be open
      assert conn._conn is not None
  ```

### Validation

```bash
uv run pytest tests/unit/test_tracker.py -v
uv run pytest tests/unit/test_download_manager.py -v
humble-track status  # Test CLI still works
```

---

## Task B.3: Break Down load_details() Method

**Priority:** Medium  
**Estimated Time:** 2-3 hours  
**Files to Modify:**

- [src/humble_tools/sync/app.py](../../../src/humble_tools/sync/app.py)

### Tasks

- [ ] **B.3.1** Extract metadata update logic

  ```python
  def _update_bundle_metadata(self) -> None:
      """Update bundle metadata display.

      Updates the metadata widget with purchase date, amount, and size.
      Should be called after bundle_data is populated.
      """
      if not self.bundle_data:
          return

      metadata = self.query_one(f"#{WidgetIds.BUNDLE_METADATA}", Static)
      meta_text = (
          f"Purchased: {self.bundle_data['purchased']} | "
          f"Amount: {self.bundle_data['amount']} | "
          f"Total Size: {self.bundle_data['total_size']}"
      )
      metadata.update(meta_text)
  ```

- [ ] **B.3.2** Extract items list population logic

  ```python
  def _populate_items_list(self) -> None:
      """Populate items list with bundle data.

      Handles empty bundles, keys-only bundles, and normal item lists.
      """
      list_view = self.query_one(f"#{WidgetIds.ITEMS_LIST}", ListView)
      list_view.clear()

      if not self.bundle_data["items"]:
          self._display_keys_or_empty(list_view)
          return

      self._add_items_header(list_view)
      self._add_items(list_view)

      # Focus first item (skip header)
      list_view.index = 1
      list_view.focus()
  ```

- [ ] **B.3.3** Extract keys display logic

  ```python
  def _display_keys_or_empty(self, list_view: ListView) -> None:
      """Display keys table or empty message.

      Args:
          list_view: ListView widget to populate
      """
      if self.bundle_data.get("keys"):
          self._display_keys(list_view)
      else:
          self._display_empty_bundle(list_view)

  def _display_keys(self, list_view: ListView) -> None:
      """Display game keys in the list view.

      Args:
          list_view: ListView widget to populate
      """
      status = self.query_one(f"#{WidgetIds.DETAILS_STATUS}", Static)
      status.update(
          f"{len(self.bundle_data['keys'])} game keys in this bundle. "
          "Visit https://www.humblebundle.com/home/keys to redeem. "
          "Press ESC to go back."
      )

      # Add header
      header_text = f"{'#':>3} | {'Key Name':60s} | {'Redeemed':>10s}"
      list_view.append(ListItem(Label(f"[bold]{header_text}[/bold]")))

      # Add keys
      for key in self.bundle_data["keys"]:
          redeemed_str = (
              f"{StatusSymbols.DOWNLOADED} Yes"
              if key["redeemed"]
              else "No"
          )
          redeemed_color = (
              Colors.SUCCESS if key["redeemed"] else Colors.WARNING
          )
          key_text = (
              f"{key['number']:3d} | {key['name'][:60]:60s} | "
              f"[{redeemed_color}]{redeemed_str:>10s}[/{redeemed_color}]"
          )
          list_view.append(ListItem(Label(key_text)))

      list_view.index = 1
      list_view.focus()

  def _display_empty_bundle(self, list_view: ListView) -> None:
      """Display empty bundle message.

      Args:
          list_view: ListView widget to populate
      """
      status = self.query_one(f"#{WidgetIds.DETAILS_STATUS}", Static)
      status.update(
          f"[{Colors.WARNING}]No items found in this bundle. "
          f"Press ESC to go back.[/{Colors.WARNING}]"
      )
      list_view.focus()
  ```

- [ ] **B.3.4** Extract items header and data addition

  ```python
  def _add_items_header(self, list_view: ListView) -> None:
      """Add header row to items list.

      Args:
          list_view: ListView widget
      """
      header_text = (
          f"{'#':{ITEM_NUMBER_WIDTH}} | "
          f"{'Item Name':{MAX_ITEM_NAME_DISPLAY_LENGTH}s} | "
          f"{'Formats':{FORMAT_DISPLAY_WIDTH}s} | "
          f"{'Size':>{SIZE_DISPLAY_WIDTH}s}"
      )
      list_view.append(ListItem(Label(f"[bold]{header_text}[/bold]")))

  def _add_items(self, list_view: ListView) -> None:
      """Add item rows to list view.

      Args:
          list_view: ListView widget
      """
      for item in self.bundle_data["items"]:
          list_view.append(
              ItemFormatRow(
                  item_number=item["number"],
                  item_name=item["name"],
                  formats=item["formats"],
                  item_size=item["size"],
                  format_status=item["format_status"],
              )
          )
  ```

- [ ] **B.3.5** Extract error handling

  ```python
  def _handle_load_error(self, error: HumbleCLIError) -> None:
      """Handle error loading bundle details.

      Args:
          error: The CLI error that occurred
      """
      api_error = APIError(
          message=str(error),
          user_message="Failed to load bundle details from Humble Bundle. "
                      "Please try again.",
      )
      logging.error(f"Failed to load bundle details: {error}")

      status = self.query_one(f"#{WidgetIds.DETAILS_STATUS}", Static)
      status.update(f"[red]{api_error.user_message}[/red]")
  ```

- [ ] **B.3.6** Simplify main `load_details()` method
  ```python
  @work(exclusive=True)
  async def load_details(self) -> None:
      """Load bundle details in background."""
      try:
          # Fetch data
          bundle_data = self.download_manager.get_bundle_items(self.bundle_key)
          self.bundle_data = bundle_data

          # Update UI
          self._update_bundle_metadata()
          self._populate_items_list()
          self.update_download_counter()

      except HumbleCLIError as e:
          self._handle_load_error(e)
  ```

### Validation

```bash
uv run pytest tests/integration/test_integration_screens.py -v
# Manual testing in TUI
humble-sync
```

---

## Task B.4: Standardize Error Handling Patterns

**Priority:** Medium  
**Estimated Time:** 2-3 hours  
**Files to Modify:**

- All files with exception handling (app.py, humble_wrapper.py, download_manager.py, etc.)

### Tasks

- [ ] **B.4.1** Document error handling strategy in docstring or comment

  ```python
  """
  Error Handling Strategy:

  1. Expected errors: Catch specific exceptions, wrap if needed, show user message
     - HumbleCLIError -> APIError with user-friendly message
     - ValidationError -> Show validation message
     - DownloadError -> Show download failure message

  2. Unexpected errors: Log with logging.exception(), show generic message
     - Catch Exception, log full traceback
     - Show generic "unexpected error" to user

  3. Recoverable errors: Return None or Result type
     - Widget queries that may fail (screen not mounted)
     - Optional operations

  4. Fatal errors: Let exception propagate
     - Programming errors (assertions)
     - System errors that can't be recovered
  """
  ```

- [ ] **B.4.2** Create error handling helpers

  ```python
  # In humble_tools/core/exceptions.py or new error_handling.py

  from typing import Callable, TypeVar, Optional
  import logging

  T = TypeVar('T')

  def safe_ui_operation(
      operation: Callable[[], T],
      default: Optional[T] = None,
      operation_name: str = "UI operation"
  ) -> Optional[T]:
      """Safely execute a UI operation that may fail.

      Args:
          operation: Function to execute
          default: Default value if operation fails
          operation_name: Name for logging

      Returns:
          Operation result or default value
      """
      try:
          return operation()
      except NoMatches:
          logging.debug(f"{operation_name} failed: widget not found")
          return default
      except Exception:
          logging.exception(f"Unexpected error in {operation_name}")
          return default
  ```

- [ ] **B.4.3** Replace bare `except Exception:` blocks with specific exceptions

  ```python
  # Before:
  try:
      notif.update(message)
  except Exception:
      logging.exception("Error")
      pass

  # After:
  try:
      notif.update(message)
  except (NoMatches, RuntimeError) as e:
      logging.warning(f"Failed to update notification: {e}")
  except Exception:
      logging.exception("Unexpected error updating notification")
      # Consider: should we re-raise here?
  ```

- [ ] **B.4.4** Ensure CLI errors are wrapped in APIError consistently

  ```python
  # Pattern to follow:
  try:
      result = humble_cli_operation()
  except HumbleCLIError as e:
      raise APIError(
          message=str(e),
          user_message="User-friendly description of what failed"
      ) from e
  ```

- [ ] **B.4.5** Add error recovery documentation to each exception handler

  ```python
  except DownloadError as e:
      # Recovery: Show error to user, mark download as failed, release semaphore
      self.show_notification(f"[red]{e.user_message}[/red]")
      item_row.format_downloading[format_name] = False
      item_row.update_display()
      self._queue.release()
  ```

- [ ] **B.4.6** Review and update all try-except blocks in codebase
  - Make a list of all exception handlers
  - Ensure each follows the documented strategy
  - Add comments explaining recovery strategy

### Validation

```bash
uv run pytest  # All tests should still pass
# Manual testing of error cases
```

---

## Completion Checklist

- [ ] All tasks in B.1 completed and validated
- [ ] All tasks in B.2 completed and validated
- [ ] All tasks in B.3 completed and validated
- [ ] All tasks in B.4 completed and validated
- [ ] All tests passing: `uv run pytest`
- [ ] Integration tests pass: `uv run pytest tests/integration/ -v`
- [ ] Manual TUI testing completed
- [ ] Manual CLI testing completed
- [ ] Code coverage maintained or improved
- [ ] Documentation updated
- [ ] Commit with message: "refactor: Phase B Structural Improvements - parser extraction and lifecycle management"

---

## Notes

- B.1 (parser extraction) is the most impactful task
- B.2 (connection lifecycle) prevents resource leaks
- B.3 (break down methods) improves readability significantly
- B.4 (error handling) may uncover edge cases during review
- Consider splitting B.4 across other tasks if it's too large

---

## Next Steps

After completing this phase, proceed to [REFACTOR_C_ARCHITECTURE.md](REFACTOR_C_ARCHITECTURE.md) for architecture refinement.
