# Refactor Phase C: Architecture Refinement

**Estimated Duration:** 1-2 weeks  
**Difficulty:** High  
**Impact:** High (significant architectural improvements)

---

## Overview

This phase focuses on major architectural improvements that enhance separation of concerns, improve testability, and modernize the codebase. These changes require careful planning and implementation but provide substantial long-term benefits.

---

## Task C.1: Extract DownloadOrchestrator from BundleDetailsScreen

**Priority:** High  
**Estimated Time:** 4-5 hours  
**Files to Create:**

- [src/humble_tools/sync/download_orchestrator.py](../../../src/humble_tools/sync/download_orchestrator.py)
- [tests/unit/test_download_orchestrator.py](../../../tests/unit/test_download_orchestrator.py)

**Files to Modify:**

- [src/humble_tools/sync/app.py](../../../src/humble_tools/sync/app.py)

### Tasks

- [ ] **C.1.1** Create `DownloadOrchestrator` class

  ```python
  """Download orchestration with lifecycle callbacks."""

  import logging
  from pathlib import Path
  from typing import Callable, Optional

  from humble_tools.core.download_manager import DownloadManager
  from humble_tools.core.exceptions import DownloadError, HumbleToolsError
  from humble_tools.sync.download_queue import DownloadQueue


  class DownloadCallbacks:
      """Callbacks for download lifecycle events."""

      def __init__(
          self,
          on_queued: Optional[Callable[[], None]] = None,
          on_started: Optional[Callable[[], None]] = None,
          on_progress: Optional[Callable[[int, int], None]] = None,
          on_completed: Optional[Callable[[bool, Optional[str]], None]] = None,
          on_error: Optional[Callable[[Exception], None]] = None,
      ):
          """Initialize callbacks.

          Args:
              on_queued: Called when download is queued
              on_started: Called when download starts
              on_progress: Called with (current, total) progress updates
              on_completed: Called with (success, error_message) when done
              on_error: Called when error occurs
          """
          self.on_queued = on_queued or (lambda: None)
          self.on_started = on_started or (lambda: None)
          self.on_progress = on_progress or (lambda cur, tot: None)
          self.on_completed = on_completed or (lambda success, msg: None)
          self.on_error = on_error or (lambda e: None)


  class DownloadOrchestrator:
      """Orchestrates downloads with queue management and callbacks.

      Separates download business logic from UI concerns by providing
      a clean interface with lifecycle callbacks.
      """

      def __init__(
          self,
          download_manager: DownloadManager,
          queue: DownloadQueue,
          output_dir: Path,
      ):
          """Initialize orchestrator.

          Args:
              download_manager: Manager for actual downloads
              queue: Download queue for concurrency control
              output_dir: Directory for downloaded files
          """
          self.download_manager = download_manager
          self.queue = queue
          self.output_dir = output_dir

      async def download_format(
          self,
          bundle_key: str,
          item_number: int,
          format_name: str,
          callbacks: DownloadCallbacks,
      ) -> bool:
          """Download a format with lifecycle callbacks.

          Args:
              bundle_key: Bundle identifier
              item_number: Item number in bundle
              format_name: Format to download (e.g., 'epub')
              callbacks: Lifecycle callbacks for UI updates

          Returns:
              True if download succeeded, False otherwise
          """
          # Mark as queued
          self.queue.mark_queued()
          callbacks.on_queued()

          # Acquire download slot (blocks until available)
          acquired = False
          try:
              self.queue.acquire()
              acquired = True

              # Mark as started
              self.queue.mark_started()
              callbacks.on_started()

              # Perform download
              success = self.download_manager.download_item(
                  bundle_key=bundle_key,
                  item_number=item_number,
                  format_name=format_name,
                  output_dir=self.output_dir,
              )

              # Mark as completed
              self.queue.mark_completed()
              callbacks.on_completed(success, None)

              return success

          except DownloadError as e:
              # Handle expected download errors
              logging.error(f"Download failed: {e}")
              self.queue.mark_completed()
              callbacks.on_completed(False, e.user_message)
              callbacks.on_error(e)
              return False

          except HumbleToolsError as e:
              # Handle other known errors
              logging.error(f"Error during download: {e}")
              self.queue.mark_completed()
              callbacks.on_completed(False, e.user_message)
              callbacks.on_error(e)
              return False

          except Exception as e:
              # Handle unexpected errors
              logging.exception(f"Unexpected error downloading {format_name}")
              self.queue.mark_completed()
              error_msg = "An unexpected error occurred"
              callbacks.on_completed(False, error_msg)
              callbacks.on_error(e)
              return False

          finally:
              # Always release semaphore if acquired
              if acquired:
                  self.queue.release()

      def get_queue_stats(self):
          """Get current queue statistics.

          Returns:
              QueueStats with active, queued, and max_concurrent counts
          """
          return self.queue.get_stats()
  ```

- [ ] **C.1.2** Create tests for `DownloadOrchestrator`

  ```python
  """Tests for download orchestrator."""

  import pytest
  from pathlib import Path
  from unittest.mock import Mock, MagicMock

  from humble_tools.sync.download_orchestrator import (
      DownloadOrchestrator,
      DownloadCallbacks,
  )
  from humble_tools.sync.download_queue import DownloadQueue
  from humble_tools.core.exceptions import DownloadError


  @pytest.fixture
  def mock_download_manager():
      """Create mock download manager."""
      manager = Mock()
      manager.download_item.return_value = True
      return manager


  @pytest.fixture
  def download_queue():
      """Create download queue."""
      return DownloadQueue(max_concurrent=2)


  @pytest.fixture
  def orchestrator(mock_download_manager, download_queue):
      """Create download orchestrator."""
      return DownloadOrchestrator(
          download_manager=mock_download_manager,
          queue=download_queue,
          output_dir=Path("/tmp/downloads"),
      )


  @pytest.mark.asyncio
  async def test_successful_download(orchestrator, mock_download_manager):
      """Test successful download calls all callbacks."""
      callbacks = DownloadCallbacks(
          on_queued=Mock(),
          on_started=Mock(),
          on_completed=Mock(),
      )

      result = await orchestrator.download_format(
          bundle_key="test_bundle",
          item_number=1,
          format_name="epub",
          callbacks=callbacks,
      )

      assert result is True
      callbacks.on_queued.assert_called_once()
      callbacks.on_started.assert_called_once()
      callbacks.on_completed.assert_called_once_with(True, None)
      mock_download_manager.download_item.assert_called_once()


  @pytest.mark.asyncio
  async def test_download_error_handling(orchestrator, mock_download_manager):
      """Test error handling calls error callback."""
      mock_download_manager.download_item.side_effect = DownloadError(
          "Download failed"
      )

      callbacks = DownloadCallbacks(
          on_error=Mock(),
          on_completed=Mock(),
      )

      result = await orchestrator.download_format(
          bundle_key="test_bundle",
          item_number=1,
          format_name="epub",
          callbacks=callbacks,
      )

      assert result is False
      callbacks.on_error.assert_called_once()
      callbacks.on_completed.assert_called_once()
      # Check that completed was called with success=False
      args = callbacks.on_completed.call_args[0]
      assert args[0] is False  # success
      assert args[1] is not None  # error_message


  @pytest.mark.asyncio
  async def test_queue_stats(orchestrator):
      """Test getting queue statistics."""
      stats = orchestrator.get_queue_stats()
      assert stats.active == 0
      assert stats.queued == 0
      assert stats.max_concurrent == 2
  ```

- [ ] **C.1.3** Update `BundleDetailsScreen` to use orchestrator

  ```python
  class BundleDetailsScreen(Container):
      """Screen showing bundle details and items."""

      def __init__(self, download_manager: DownloadManager, config: AppConfig):
          super().__init__()
          self.download_manager = download_manager
          self.config = config
          self.bundle_key = ""
          self.bundle_name = ""
          self.bundle_data = None

          # Create orchestrator
          self._queue = DownloadQueue(
              max_concurrent=self.config.max_concurrent_downloads
          )
          self._orchestrator = DownloadOrchestrator(
              download_manager=self.download_manager,
              queue=self._queue,
              output_dir=self.config.output_dir,
          )

      @work(thread=True)
      def download_format(self, item_row: ItemFormatRow) -> None:
          """Download the selected format for an item."""
          selected_format = item_row.selected_format
          if not selected_format:
              return

          # Create callbacks for UI updates
          callbacks = DownloadCallbacks(
              on_queued=lambda: self._handle_download_queued(
                  item_row, selected_format
              ),
              on_started=lambda: self._handle_download_started(
                  item_row, selected_format
              ),
              on_completed=lambda success, error: self._handle_download_completed(
                  item_row, selected_format, success, error
              ),
              on_error=lambda e: self._handle_download_error(
                  item_row, selected_format, e
              ),
          )

          # Delegate to orchestrator
          success = await self._orchestrator.download_format(
              bundle_key=self.bundle_key,
              item_number=item_row.item_number,
              format_name=selected_format,
              callbacks=callbacks,
          )

          # Schedule item removal if all formats downloaded
          if self._all_formats_downloaded(item_row):
              self.set_timer(
                  self.config.item_removal_delay,
                  lambda: self.maybe_remove_item(item_row),
              )
  ```

- [ ] **C.1.4** Simplify download callback handlers

  ```python
  def _handle_download_queued(
      self, item_row: ItemFormatRow, selected_format: str
  ) -> None:
      """Handle download entering queued state."""
      def update_ui():
          item_row.format_queued[selected_format] = True
          item_row.update_display()
          self.update_download_counter()

      self.app.call_from_thread(update_ui)

  def _handle_download_started(
      self, item_row: ItemFormatRow, selected_format: str
  ) -> None:
      """Handle download moving to active state."""
      def update_ui():
          item_row.format_queued[selected_format] = False
          item_row.format_downloading[selected_format] = True
          item_row.update_display()
          self.update_download_counter()

      self.app.call_from_thread(update_ui)

  def _handle_download_completed(
      self,
      item_row: ItemFormatRow,
      selected_format: str,
      success: bool,
      error_message: Optional[str],
  ) -> None:
      """Handle download completion."""
      def update_ui():
          item_row.format_downloading[selected_format] = False

          if success:
              item_row.format_status[selected_format] = True
              item_row.update_display()
              self.show_notification(
                  f"[green]Downloaded {selected_format} for {item_row.item_name}[/green]"
              )
          else:
              item_row.update_display()
              self.show_notification(
                  f"[red]{error_message or 'Download failed'}[/red]"
              )

          self.update_download_counter()

      self.app.call_from_thread(update_ui)

  def _handle_download_error(
      self, item_row: ItemFormatRow, selected_format: str, error: Exception
  ) -> None:
      """Handle download error."""
      # Error already handled in _handle_download_completed
      # This is for additional error-specific logging if needed
      logging.debug(f"Download error details: {error}")
  ```

- [ ] **C.1.5** Update `update_download_counter()` to use orchestrator
  ```python
  def update_download_counter(self) -> None:
      """Update status bar with active download count."""
      status = self._safe_query_widget(f"#{WidgetIds.DETAILS_STATUS}", Static)
      if status is None:
          return

      stats = self._orchestrator.get_queue_stats()
      queue_status = self._format_queue_status_from_stats(stats)
      items_info = self._format_items_info()

      if items_info:
          nav_help = self._format_navigation_help()
          status.update(f"{items_info} | {queue_status} | {nav_help}")
      else:
          status.update(queue_status)
  ```

### Validation

```bash
uv run pytest tests/unit/test_download_orchestrator.py -v
uv run pytest tests/integration/ -v
# Manual TUI testing
humble-sync
```

---

## Task C.2: Evaluate and Simplify Database Protocol Usage

**Priority:** Medium  
**Estimated Time:** 2-3 hours  
**Files to Evaluate:**

- [src/humble_tools/core/database.py](../../../src/humble_tools/core/database.py)
- [src/humble_tools/core/tracker.py](../../../src/humble_tools/core/tracker.py)
- [tests/unit/test_database.py](../../../tests/unit/test_database.py)
- [tests/unit/test_tracker.py](../../../tests/unit/test_tracker.py)

### Tasks

- [ ] **C.2.1** Analyze Protocol usage in tests

  ```bash
  # Search for DatabaseConnection usage in tests
  grep -r "DatabaseConnection" tests/
  # Check if mock connections are used
  grep -r "Mock.*Connection" tests/
  ```

- [ ] **C.2.2** Document findings

  - [ ] List all places where `DatabaseConnection` Protocol is used
  - [ ] Identify if any non-SQLite implementations exist or are planned
  - [ ] Check if tests mock the connection
  - [ ] Evaluate if Protocol provides real testing benefits

- [ ] **C.2.3** **Decision Point: Keep or Remove Protocol?**

  **Option A: Keep Protocol (if actively used in tests)**

  - [ ] Document why Protocol is beneficial
  - [ ] Add more Protocol implementations if needed (e.g., `InMemoryConnection`)
  - [ ] Ensure all implementations follow Protocol correctly

  **Option B: Remove Protocol (if not providing value)**

  - [ ] Replace `DatabaseConnection` Protocol with concrete `SQLiteConnection`
  - [ ] Update type hints:

    ```python
    # Before:
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):

    # After:
    def __init__(self, db_connection: Optional[SQLiteConnection] = None):
    ```

  - [ ] Remove Protocol class from `database.py`
  - [ ] Update imports throughout codebase
  - [ ] Update tests to use concrete class

- [ ] **C.2.4** If keeping Protocol, add better documentation

  ```python
  class DatabaseConnection(Protocol):
      """Protocol for database connection interface.

      This Protocol allows for multiple database implementations and
      simplified testing with mock connections.

      Implementations:
          - SQLiteConnection: Production SQLite database
          - MockConnection (in tests): In-memory mock for testing

      Why Protocol:
          - Enables dependency injection for testing
          - Allows future database backends without code changes
          - Maintains clean separation between database interface and implementation
      """
  ```

- [ ] **C.2.5** If removing Protocol, document decision

  ```python
  # In database.py or design docs
  """
  Design Decision: Direct SQLite Usage

  We removed the DatabaseConnection Protocol abstraction because:
  1. Only SQLite implementation exists and none planned
  2. Tests don't require mock connections (use :memory: SQLite)
  3. Protocol adds complexity without benefit (YAGNI)
  4. SQLite is sufficient for this application's needs

  If future database backends are needed, a Protocol can be reintroduced.
  """
  ```

### Validation

```bash
uv run pytest tests/unit/test_database.py -v
uv run pytest tests/unit/test_tracker.py -v
uv run pytest  # All tests should pass
```

---

## Task C.3: Migrate to Pydantic for Configuration

**Priority:** Medium  
**Estimated Time:** 2-3 hours  
**Files to Modify:**

- [pyproject.toml](../../../pyproject.toml) (add Pydantic dependency)
- [src/humble_tools/sync/config.py](../../../src/humble_tools/sync/config.py)
- [tests/unit/test_config.py](../../../tests/unit/test_config.py)

### Tasks

- [ ] **C.3.1** Add Pydantic dependency

  ```bash
  uv add pydantic
  ```

- [ ] **C.3.2** Convert `AppConfig` to Pydantic model

  ```python
  """Configuration for the Humble Bundle TUI application."""

  from pathlib import Path

  from pydantic import BaseModel, Field, field_validator

  from humble_tools.sync.constants import (
      DEFAULT_MAX_CONCURRENT_DOWNLOADS,
      DEFAULT_OUTPUT_DIR,
      ITEM_REMOVAL_DELAY_SECONDS,
      NOTIFICATION_DURATION_SECONDS,
  )


  class AppConfig(BaseModel):
      """Configuration for the Humble Bundle TUI application.

      Uses Pydantic for validation and better error messages.
      """

      max_concurrent_downloads: int = Field(
          default=DEFAULT_MAX_CONCURRENT_DOWNLOADS,
          ge=1,
          le=10,
          description="Maximum number of simultaneous downloads"
      )

      notification_duration: int = Field(
          default=NOTIFICATION_DURATION_SECONDS,
          ge=1,
          description="How long notifications are displayed (seconds)"
      )

      item_removal_delay: int = Field(
          default=ITEM_REMOVAL_DELAY_SECONDS,
          ge=0,
          description="Delay before removing completed items (seconds)"
      )

      output_dir: Path = Field(
          default=DEFAULT_OUTPUT_DIR,
          description="Directory where downloaded files are saved"
      )

      @field_validator('output_dir', mode='before')
      @classmethod
      def ensure_path(cls, v):
          """Ensure output_dir is a Path object."""
          return Path(v) if not isinstance(v, Path) else v

      @field_validator('output_dir')
      @classmethod
      def create_output_dir(cls, v: Path) -> Path:
          """Create output directory if it doesn't exist."""
          v.mkdir(parents=True, exist_ok=True)
          return v

      model_config = {
          "arbitrary_types_allowed": True,
          "frozen": False,  # Allow mutation if needed
      }
  ```

- [ ] **C.3.3** Update tests to use Pydantic model

  ```python
  """Tests for application configuration."""

  import pytest
  from pathlib import Path
  from pydantic import ValidationError

  from humble_tools.sync.config import AppConfig


  def test_default_config():
      """Test default configuration values."""
      config = AppConfig()
      assert config.max_concurrent_downloads == 3
      assert config.notification_duration == 5
      assert config.item_removal_delay == 10
      assert isinstance(config.output_dir, Path)


  def test_custom_config():
      """Test custom configuration values."""
      config = AppConfig(
          max_concurrent_downloads=5,
          notification_duration=10,
          output_dir="/tmp/downloads"
      )
      assert config.max_concurrent_downloads == 5
      assert config.notification_duration == 10
      assert isinstance(config.output_dir, Path)
      assert config.output_dir == Path("/tmp/downloads")


  def test_invalid_max_concurrent():
      """Test validation of max_concurrent_downloads."""
      with pytest.raises(ValidationError) as exc_info:
          AppConfig(max_concurrent_downloads=0)
      assert "greater than or equal to 1" in str(exc_info.value)


  def test_invalid_notification_duration():
      """Test validation of notification_duration."""
      with pytest.raises(ValidationError) as exc_info:
          AppConfig(notification_duration=0)
      assert "greater than or equal to 1" in str(exc_info.value)


  def test_negative_item_removal_delay():
      """Test validation of item_removal_delay."""
      with pytest.raises(ValidationError) as exc_info:
          AppConfig(item_removal_delay=-1)
      assert "greater than or equal to 0" in str(exc_info.value)


  def test_path_conversion():
      """Test automatic path conversion."""
      config = AppConfig(output_dir="/tmp/test")
      assert isinstance(config.output_dir, Path)
      assert config.output_dir == Path("/tmp/test")


  def test_config_immutability_optional():
      """Test that config can be modified if needed."""
      config = AppConfig()
      config.max_concurrent_downloads = 5
      assert config.max_concurrent_downloads == 5
  ```

- [ ] **C.3.4** Add environment variable support (optional enhancement)

  ```python
  from pydantic_settings import BaseSettings, SettingsConfigDict

  class AppConfig(BaseSettings):
      """Configuration with environment variable support."""

      max_concurrent_downloads: int = Field(
          default=DEFAULT_MAX_CONCURRENT_DOWNLOADS,
          ge=1,
          le=10,
      )
      # ... other fields

      model_config = SettingsConfigDict(
          env_prefix='HUMBLE_',  # HUMBLE_MAX_CONCURRENT_DOWNLOADS
          env_file='.env',
          env_file_encoding='utf-8',
          arbitrary_types_allowed=True,
      )
  ```

- [ ] **C.3.5** Update any code that catches `ValueError` from validation

  ```python
  # Before:
  try:
      config = AppConfig(max_concurrent_downloads=0)
  except ValueError as e:
      print(f"Invalid config: {e}")

  # After:
  from pydantic import ValidationError

  try:
      config = AppConfig(max_concurrent_downloads=0)
  except ValidationError as e:
      print(f"Invalid config: {e}")
  ```

### Validation

```bash
uv run pytest tests/unit/test_config.py -v
uv run pytest  # All tests should pass
```

---

## Task C.4: Add Type Checking with ty

**Priority:** Medium  
**Estimated Time:** 3-4 hours  
**Files to Create/Modify:**

- [pyproject.toml](../../../pyproject.toml) (add type checking config)
- Various source files (fix type issues)

### Tasks

- [ ] **C.4.1** Add ty as dev dependency

  ```bash
  # ty - Modern, fast type checker
  uv add --dev ty
  ```

- [ ] **C.4.2** Add type checking configuration to `pyproject.toml`

  ```toml
  [tool.ty]
  include = ["src"]
  exclude = ["**/__pycache__", "**/.venv"]

  python_version = "3.8"
  strict = false  # Start with basic, move to strict later

  warn_unused_imports = true
  warn_unused_variables = true
  warn_return_any = true
  warn_unreachable = true
  disallow_untyped_defs = false  # Enable gradually
  disallow_incomplete_defs = false  # Enable gradually
  ```

- [ ] **C.4.3** Run type checker and fix issues

  ```bash
  uv run ty src/humble_tools
  ```

- [ ] **C.4.4** Common type issues to fix:

  - [ ] Add return type hints to all functions
  - [ ] Fix `Optional[x]` vs `x | None` consistency
  - [ ] Add type hints to lambdas where possible
  - [ ] Fix `Any` types to be more specific
  - [ ] Add `typing.cast()` where type narrowing is needed
  - [ ] Fix generic type parameters

- [ ] **C.4.5** Add type ignore comments sparingly

  ```python
  # Only use when absolutely necessary
  result = some_untyped_library_call()  # type: ignore[no-untyped-call]
  ```

- [ ] **C.4.6** Add type stubs for third-party libraries if needed

  ```bash
  # If textual doesn't have types:
  uv add --dev types-textual
  ```

- [ ] **C.4.7** Add type checking to pre-commit hooks

  ```yaml
  # In .pre-commit-config.yaml
  repos:
    # ... existing hooks
    - repo: local
      hooks:
        - id: ty
          name: ty
          entry: uv run ty
          language: system
          types: [python]
          pass_filenames: false
  ```

- [ ] **C.4.8** Add type checking to CI (future task for Phase D)
  ```yaml
  # Note: Add to GitHub Actions in Phase D
  - name: Type check
    run: uv run ty src/humble_tools
  ```

### Validation

```bash
uv run ty src/humble_tools
# Should report 0 errors
uv run pytest  # All tests should still pass
```

---

## Completion Checklist

- [ ] All tasks in C.1 completed and validated
- [ ] All tasks in C.2 completed and validated
- [ ] All tasks in C.3 completed and validated
- [ ] All tasks in C.4 completed and validated
- [ ] All tests passing: `uv run pytest`
- [ ] Type checking passes: `uv run ty src/humble_tools`
- [ ] Integration tests pass: `uv run pytest tests/integration/ -v`
- [ ] Manual testing completed (both CLI and TUI)
- [ ] Documentation updated
- [ ] Commit with message: "refactor: Phase C Architecture Refinement - orchestrator extraction and modern tooling"

---

## Notes

- C.1 (orchestrator) is the most complex task, take time with it
- C.2 (Protocol evaluation) is a decision-making task, document reasoning
- C.3 (Pydantic) provides better validation and error messages
- C.4 (type checking) catches many bugs before runtime
- This phase significantly improves code quality and maintainability
- Consider breaking this into multiple smaller commits

---

## Next Steps

After completing this phase, proceed to [REFACTOR_D_TOOLING.md](REFACTOR_D_TOOLING.md) for tooling and quality improvements.
