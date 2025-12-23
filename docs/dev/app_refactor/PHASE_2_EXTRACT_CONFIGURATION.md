# Phase 2: Extract Configuration & Constants - Detailed Task Document

**Date Created:** December 22, 2025  
**Status:** Ready for Implementation  
**Priority:** HIGH  
**Estimated Effort:** 1-2 hours  
**Risk Level:** Low  
**Dependencies:** Phase 1 (Critical Fixes) must be completed first

---

## Overview

Phase 2 focuses on extracting magic numbers, hard-coded strings, and configuration values into well-organized constants and configuration structures. This improves maintainability, makes the codebase more testable, and prepares for future configuration file support.

### Goals

- ✅ Eliminate all magic numbers from app.py
- ✅ Extract hard-coded strings to constants
- ✅ Create reusable configuration dataclass
- ✅ Improve code readability and maintainability
- ✅ Enable future configuration file support

### Success Criteria

- [x] Zero magic numbers in app.py
- [x] All timing values configurable
- [x] All display dimensions in constants
- [x] All status messages in constants
- [x] Configuration can be passed to TUI app
- [x] All existing functionality preserved
- [x] No behavioral changes

---

## Prerequisites

⚠️ **CRITICAL:** Phase 1 must be completed before starting Phase 2:

- [x] `async` keyword removed from `download_format` method
- [x] `_download_lock` added and used for counter protection
- [x] Broad exception handlers fixed
- [x] Semaphore release properly guarded

If Phase 1 is not complete, complete it first before proceeding.

---

## Task 1: Create Constants Module

**Priority:** HIGH  
**Estimated Time:** 20 minutes  
**File:** NEW - `src/humble_tools/sync/constants.py`

### Implementation

Create a new file with well-organized constants grouped by category.

```python
"""Constants and configuration values for Humble Bundle TUI."""

from enum import Enum
from pathlib import Path


# === Download Settings ===

MAX_CONCURRENT_DOWNLOADS = 3
"""Maximum number of simultaneous downloads allowed."""

NOTIFICATION_DURATION_SECONDS = 5
"""How long to show notification messages."""

ITEM_REMOVAL_DELAY_SECONDS = 10
"""Delay before removing completed items from list."""


# === Display Dimensions ===

ITEM_NUMBER_WIDTH = 3
"""Width for item number column."""

ITEM_NAME_WIDTH = 50
"""Width for item name column (truncated with ...)."""

ITEM_SIZE_WIDTH = 10
"""Width for item size column."""


# === Widget IDs ===

class WidgetID:
    """Widget ID constants for query selectors."""

    BUNDLE_LIST = "bundle-list"
    DETAILS_LIST = "details-list"
    DETAILS_STATUS = "details-status"
    BUNDLES_CONTAINER = "bundles-container"
    DETAILS_CONTAINER = "details-container"


# === Status Messages ===

class StatusMessage:
    """Pre-formatted status messages."""

    # Download states
    DOWNLOAD_SUCCESS = "[green]✓ Downloaded: {item_name} ({format})[/green]"
    DOWNLOAD_FAILED = "[red]✗ Failed: {item_name} ({format})[/red]"
    DOWNLOAD_ERROR = "[red]Error: {error}[/red]"

    # Queue info
    ACTIVE_DOWNLOADS = "Active Downloads: {active}/{max}"
    ACTIVE_AND_QUEUED = "Active: {active}/{max} | Queued: {queued}"

    # Bundle operations
    LOADING_BUNDLES = "Loading bundles..."
    NO_BUNDLES = "No bundles found"
    LOADING_DETAILS = "Loading bundle details..."

    # Errors
    ERROR_LOADING_BUNDLES = "[red]Error loading bundles: {error}[/red]"
    ERROR_LOADING_DETAILS = "[red]Error loading details: {error}[/red]"


# === Status Indicators ===

class StatusIndicator:
    """Visual indicators for download status."""

    DOWNLOADED = "✓"
    DOWNLOADING = "↓"
    QUEUED = "⏱"
    AVAILABLE = " "


# === Default Paths ===

DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "HumbleBundle"
"""Default directory for downloaded files."""


# === Format Display ===

FORMAT_SEPARATOR = " / "
"""Separator between multiple formats."""

TRUNCATION_INDICATOR = "..."
"""Indicator for truncated text."""
```

### Steps

1. Create `src/humble_tools/sync/constants.py`
2. Copy the code above
3. Save and verify it imports correctly:
   ```bash
   cd /home/varigg/projects/python/humblebundle
   python -c "from src.humble_tools.sync.constants import MAX_CONCURRENT_DOWNLOADS; print(MAX_CONCURRENT_DOWNLOADS)"
   ```

### Verification

- [x] File created at correct location
- [x] Imports successfully
- [x] No syntax errors
- [x] All constants properly documented

---

## Task 2: Create Configuration Dataclass

**Priority:** HIGH  
**Estimated Time:** 15 minutes  
**File:** NEW - `src/humble_tools/sync/config.py`

### Implementation

Create a configuration dataclass that can be instantiated with custom values.

```python
"""Configuration for Humble Bundle TUI application."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .constants import (
    MAX_CONCURRENT_DOWNLOADS,
    NOTIFICATION_DURATION_SECONDS,
    ITEM_REMOVAL_DELAY_SECONDS,
    DEFAULT_OUTPUT_DIR,
)


@dataclass
class AppConfig:
    """Configuration for HumbleBundleTUI application.

    Attributes:
        max_concurrent_downloads: Maximum simultaneous downloads (default: 3)
        notification_duration: Seconds to show notifications (default: 5)
        item_removal_delay: Seconds before removing completed items (default: 10)
        output_dir: Directory for downloaded files
        session_file: Optional path to Humble Bundle session file
    """

    max_concurrent_downloads: int = MAX_CONCURRENT_DOWNLOADS
    notification_duration: int = NOTIFICATION_DURATION_SECONDS
    item_removal_delay: int = ITEM_REMOVAL_DELAY_SECONDS
    output_dir: Path = field(default_factory=lambda: DEFAULT_OUTPUT_DIR)
    session_file: Optional[Path] = None

    def __post_init__(self):
        """Validate configuration values."""
        if self.max_concurrent_downloads < 1:
            raise ValueError("max_concurrent_downloads must be at least 1")
        if self.max_concurrent_downloads > 10:
            raise ValueError("max_concurrent_downloads should not exceed 10")

        if self.notification_duration < 1:
            raise ValueError("notification_duration must be at least 1")

        if self.item_removal_delay < 0:
            raise ValueError("item_removal_delay must be non-negative")

        # Ensure output_dir is a Path object
        if not isinstance(self.output_dir, Path):
            self.output_dir = Path(self.output_dir)

    @classmethod
    def from_dict(cls, config_dict: dict) -> "AppConfig":
        """Create config from dictionary (for loading from file).

        Args:
            config_dict: Dictionary with configuration values

        Returns:
            AppConfig instance
        """
        # Convert string paths to Path objects
        if "output_dir" in config_dict:
            config_dict["output_dir"] = Path(config_dict["output_dir"])
        if "session_file" in config_dict and config_dict["session_file"]:
            config_dict["session_file"] = Path(config_dict["session_file"])

        return cls(**config_dict)
```

### Steps

1. Create `src/humble_tools/sync/config.py`
2. Copy the code above
3. Test configuration validation:
   ```bash
   python -c "from src.humble_tools.sync.config import AppConfig; c = AppConfig(); print(c)"
   ```

### Verification

- [x] File created successfully
- [x] Imports successfully
- [x] Default values work
- [x] Validation catches invalid values
- [x] `from_dict` method works

---

## Task 3: Update app.py to Import Constants

**Priority:** HIGH  
**Estimated Time:** 10 minutes  
**File:** `src/humble_tools/sync/app.py`

### Implementation

Add imports at the top of the file (after existing imports, around line 18).

```python
from humble_tools.core.download_manager import DownloadManager
from humble_tools.core.humble_wrapper import HumbleCLIError, get_bundles
from humble_tools.core.tracker import DownloadTracker
from .config import AppConfig  # NEW
from .constants import (  # NEW
    MAX_CONCURRENT_DOWNLOADS,
    NOTIFICATION_DURATION_SECONDS,
    ITEM_REMOVAL_DELAY_SECONDS,
    ITEM_NUMBER_WIDTH,
    ITEM_NAME_WIDTH,
    ITEM_SIZE_WIDTH,
    FORMAT_SEPARATOR,
    TRUNCATION_INDICATOR,
    StatusIndicator,
    StatusMessage,
    WidgetID,
)
```

### Steps

1. Open `src/humble_tools/sync/app.py`
2. Locate the import section (lines 1-18)
3. Add the new imports after line 18
4. Save the file

### Verification

- [x] File imports successfully
- [x] No import errors
- [x] Application still starts

---

## Task 4: Replace Magic Numbers in BundleDetailsScreen.**init**

**Priority:** HIGH  
**Estimated Time:** 10 minutes  
**File:** `src/humble_tools/sync/app.py`
**Lines:** ~220-235

### Current Code

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

### New Code

```python
    def __init__(
        self,
        epub_manager: DownloadManager,
        output_dir: Path,
        config: Optional[AppConfig] = None,
    ):
        super().__init__()
        self.config = config or AppConfig()
        self.epub_manager = epub_manager
        self.output_dir = output_dir
        self.bundle_key = ""
        self.bundle_name = ""
        self.bundle_data = None
        self.active_downloads = 0
        self.queued_downloads = 0
        self.max_concurrent_downloads = self.config.max_concurrent_downloads
        self._download_semaphore = threading.Semaphore(self.max_concurrent_downloads)
        self._download_lock = threading.Lock()  # From Phase 1
```

### Steps

1. Locate `BundleDetailsScreen.__init__` method
2. Add `config: Optional[AppConfig] = None` parameter
3. Add `self.config = config or AppConfig()` at the start
4. Replace `3` with `self.config.max_concurrent_downloads`
5. Save file

### Verification

- [x] Method signature updated
- [x] Config properly stored
- [x] Default config created if none provided
- [x] Max concurrent downloads comes from config

---

## Task 5: Replace Widget ID Strings

**Priority:** MEDIUM  
**Estimated Time:** 15 minutes  
**File:** `src/humble_tools/sync/app.py`
**Multiple locations**

### Locations to Update

1. **Line ~240** - `query_one("#details-status", Static)`
2. **Line ~348** - `query_one("#bundles-container", Container)`
3. **Line ~349** - `query_one("#details-container", Container)`
4. **Line ~403** - `query_one("#details-list", ListView)`
5. **Line ~571** - `query_one("#bundle-list", ListView)`

### Changes

Replace all hard-coded widget IDs with constants:

```python
# Before
status = self.query_one("#details-status", Static)

# After
status = self.query_one(f"#{WidgetID.DETAILS_STATUS}", Static)
```

Or even better, add a helper method:

```python
def _widget_id(self, name: str) -> str:
    """Convert widget ID constant to selector string.

    Args:
        name: Widget ID from WidgetID constants

    Returns:
        Formatted selector string (#id)
    """
    return f"#{name}"
```

Then use:

```python
status = self.query_one(self._widget_id(WidgetID.DETAILS_STATUS), Static)
```

### Implementation Steps

1. **Add helper method** to `HumbleBundleTUI` class (optional but recommended)
2. **Find and replace** each hard-coded ID:

   - `"#details-status"` → `f"#{WidgetID.DETAILS_STATUS}"`
   - `"#bundles-container"` → `f"#{WidgetID.BUNDLES_CONTAINER}"`
   - `"#details-container"` → `f"#{WidgetID.DETAILS_CONTAINER}"`
   - `"#details-list"` → `f"#{WidgetID.DETAILS_LIST}"`
   - `"#bundle-list"` → `f"#{WidgetID.BUNDLE_LIST}"`

3. **Update compose methods** to use constants in widget ID assignments

### Verification

- [x] All widget IDs replaced
- [x] Application still functions
- [x] No query errors in logs

---

## Task 6: Replace Status Messages

**Priority:** MEDIUM  
**Estimated Time:** 20 minutes  
**File:** `src/humble_tools/sync/app.py\*\*
**Multiple locations in download_format method**

### Locations to Update

1. **Success notification** (~line 510)
2. **Failure notification** (~line 521)
3. **Error notification** (~line 530)
4. **Download counter display** (~line 246-251)

### Changes

**Success message:**

```python
# Before
self.show_notification(
    f"[green]✓ Downloaded: {item_row.item_name} ({selected_format})[/green]",
    duration=5,
)

# After
self.show_notification(
    StatusMessage.DOWNLOAD_SUCCESS.format(
        item_name=item_row.item_name,
        format=selected_format
    ),
    duration=self.config.notification_duration,
)
```

**Failure message:**

```python
# Before
self.show_notification(
    f"[red]✗ Failed: {item_row.item_name} ({selected_format})[/red]",
    duration=5,
)

# After
self.show_notification(
    StatusMessage.DOWNLOAD_FAILED.format(
        item_name=item_row.item_name,
        format=selected_format
    ),
    duration=self.config.notification_duration,
)
```

**Error message:**

```python
# Before
self.show_notification(f"[red]Error: {error_msg}[/red]", duration=5)

# After
self.show_notification(
    StatusMessage.DOWNLOAD_ERROR.format(error=error_msg),
    duration=self.config.notification_duration,
)
```

**Counter display:**

```python
# Before
if self.queued_downloads > 0:
    queue_info = (
        f"Active: {self.active_downloads}/{self.max_concurrent_downloads} | Queued: {self.queued_downloads}"
    )
else:
    queue_info = (
        f"Active Downloads: {self.active_downloads}/{self.max_concurrent_downloads}"
    )

# After
if self.queued_downloads > 0:
    queue_info = StatusMessage.ACTIVE_AND_QUEUED.format(
        active=self.active_downloads,
        max=self.max_concurrent_downloads,
        queued=self.queued_downloads,
    )
else:
    queue_info = StatusMessage.ACTIVE_DOWNLOADS.format(
        active=self.active_downloads,
        max=self.max_concurrent_downloads,
    )
```

### Implementation Steps

1. Replace all notification calls with formatted StatusMessage constants
2. Replace duration=5 with duration=self.config.notification_duration
3. Update download counter display logic
4. Save file

### Verification

- [x] All messages use StatusMessage constants
- [x] Duration comes from config
- [x] Messages display correctly
- [x] Formatting preserved

---

## Task 7: Replace Display Constants in ItemFormatRow

**Priority:** MEDIUM  
**Estimated Time:** 15 minutes  
**File:** `src/humble_tools/sync/app.py`
**Class:** `ItemFormatRow`
**Method:** `_build_display_text`

### Locations to Update

In the `_build_display_text` method (~lines 95-130):

1. Item number width (currently `3`)
2. Item name width (currently `50`)
3. Item size width (currently `10`)
4. Truncation indicator (`"..."`)
5. Format separator (`" / "`)
6. Status indicators (`"✓"`, `"↓"`, `"⏱"`, `" "`)

### Changes

```python
# Before
def _build_display_text(self) -> str:
    # Item number (right-aligned, 3 chars)
    num_str = f"{self.item_number:>3}"

    # Item name (left-aligned, truncate if > 50 chars)
    name_str = self.item_name[:50]
    if len(self.item_name) > 50:
        name_str = name_str[:47] + "..."
    name_str = f"{name_str:<50}"

    # Item size (right-aligned, 10 chars)
    size_str = f"{self.item_size:>10}"

    # Format list with status
    format_parts = []
    for fmt in self.formats:
        # Status indicator
        if self.format_status.get(fmt, False):
            indicator = "✓"
        elif self.format_downloading.get(fmt, False):
            indicator = "↓"
        elif self.format_queued.get(fmt, False):
            indicator = "⏱"
        else:
            indicator = " "

        # Format display
        format_parts.append(f"[{indicator}] {fmt}")

    formats_str = " / ".join(format_parts)

# After
def _build_display_text(self) -> str:
    # Item number (right-aligned)
    num_str = f"{self.item_number:>{ITEM_NUMBER_WIDTH}}"

    # Item name (left-aligned, truncate if needed)
    name_str = self.item_name[:ITEM_NAME_WIDTH]
    if len(self.item_name) > ITEM_NAME_WIDTH:
        truncate_at = ITEM_NAME_WIDTH - len(TRUNCATION_INDICATOR)
        name_str = name_str[:truncate_at] + TRUNCATION_INDICATOR
    name_str = f"{name_str:<{ITEM_NAME_WIDTH}}"

    # Item size (right-aligned)
    size_str = f"{self.item_size:>{ITEM_SIZE_WIDTH}}"

    # Format list with status
    format_parts = []
    for fmt in self.formats:
        # Status indicator
        if self.format_status.get(fmt, False):
            indicator = StatusIndicator.DOWNLOADED
        elif self.format_downloading.get(fmt, False):
            indicator = StatusIndicator.DOWNLOADING
        elif self.format_queued.get(fmt, False):
            indicator = StatusIndicator.QUEUED
        else:
            indicator = StatusIndicator.AVAILABLE

        # Format display
        format_parts.append(f"[{indicator}] {fmt}")

    formats_str = FORMAT_SEPARATOR.join(format_parts)
```

### Implementation Steps

1. Locate `_build_display_text` method
2. Replace all magic numbers with constants
3. Replace status indicators with StatusIndicator constants
4. Replace `" / "` with `FORMAT_SEPARATOR`
5. Replace `"..."` with `TRUNCATION_INDICATOR`
6. Save file

### Verification

- [x] Display formatting unchanged
- [x] Status indicators work correctly
- [x] Truncation works as before
- [x] Format separation correct

---

## Task 8: Update Item Removal Delay

**Priority:** LOW  
**Estimated Time:** 5 minutes  
**File:** `src/humble_tools/sync/app.py`
**Line:** ~512

### Current Code

```python
# Schedule item removal if all formats downloaded
self.set_timer(10, lambda: self.maybe_remove_item(item_row))
```

### New Code

```python
# Schedule item removal if all formats downloaded
self.set_timer(
    self.config.item_removal_delay,
    lambda: self.maybe_remove_item(item_row)
)
```

### Steps

1. Find the `set_timer` call in the success callback
2. Replace `10` with `self.config.item_removal_delay`
3. Save file

### Verification

- [x] Timer uses config value
- [x] Items still removed after delay
- [x] No timing issues

---

## Task 9: Update HumbleBundleTUI.**init** to Accept Config

**Priority:** HIGH  
**Estimated Time:** 10 minutes  
**File:** `src/humble_tools/sync/app.py`
**Class:** `HumbleBundleTUI`

### Current Code

```python
def __init__(self, session_file: Optional[Path] = None):
    super().__init__()
    self.session_file = session_file
    self.epub_manager = None
    self.output_dir = Path.home() / "Downloads" / "HumbleBundle"
```

### New Code

```python
def __init__(
    self,
    session_file: Optional[Path] = None,
    config: Optional[AppConfig] = None,
):
    super().__init__()
    self.config = config or AppConfig()
    self.session_file = session_file or self.config.session_file
    self.epub_manager = None
    self.output_dir = self.config.output_dir
```

### Steps

1. Locate `HumbleBundleTUI.__init__` method
2. Add `config` parameter
3. Store config and use it for output_dir
4. Update session_file to fall back to config
5. Save file

### Verification

- [x] Config parameter added
- [x] Default config created if needed
- [x] Output dir comes from config
- [x] Session file prioritized correctly

---

## Task 10: Pass Config to BundleDetailsScreen

**Priority:** HIGH  
**Estimated Time:** 10 minutes  
**File:** `src/humble_tools/sync/app.py`
**Method:** `HumbleBundleTUI.on_mount`

### Current Code

```python
# Create bundle details screen
self.details_screen = BundleDetailsScreen(
    epub_manager=self.epub_manager,
    output_dir=self.output_dir,
)
```

### New Code

```python
# Create bundle details screen
self.details_screen = BundleDetailsScreen(
    epub_manager=self.epub_manager,
    output_dir=self.output_dir,
    config=self.config,
)
```

### Steps

1. Find where `BundleDetailsScreen` is instantiated
2. Add `config=self.config` parameter
3. Save file

### Verification

- [x] Config passed to details screen
- [x] Screen uses config values
- [x] No errors on instantiation

---

## Task 11: Update CLI Entry Point (Optional)

**Priority:** LOW  
**Estimated Time:** 15 minutes  
**File:** Check if there's a CLI entry point that needs updating

### Implementation

If the TUI is launched from a CLI:

```python
# Example CLI integration
def run_tui(session_file: Optional[Path] = None, config_file: Optional[Path] = None):
    """Run the Humble Bundle TUI.

    Args:
        session_file: Path to Humble Bundle session file
        config_file: Path to configuration file (TOML/JSON)
    """
    config = None
    if config_file and config_file.exists():
        # Load config from file
        import tomllib  # Python 3.11+ or use tomli for older versions
        with open(config_file, 'rb') as f:
            config_dict = tomllib.load(f)
            config = AppConfig.from_dict(config_dict)

    app = HumbleBundleTUI(session_file=session_file, config=config)
    app.run()
```

### Steps

1. Locate CLI entry point (if exists)
2. Add config file support
3. Update to pass config to TUI
4. Save file

### Verification

- [x] CLI accepts config file
- [x] Config loaded correctly
- [x] TUI uses config values

---

## Testing Checklist

### Unit Tests (Optional but Recommended)

Create `tests/test_config.py`:

```python
"""Tests for configuration module."""

import pytest
from pathlib import Path
from humble_tools.sync.config import AppConfig


def test_default_config():
    """Test default configuration values."""
    config = AppConfig()
    assert config.max_concurrent_downloads == 3
    assert config.notification_duration == 5
    assert config.item_removal_delay == 10
    assert config.output_dir == Path.home() / "Downloads" / "HumbleBundle"
    assert config.session_file is None


def test_custom_config():
    """Test custom configuration values."""
    config = AppConfig(
        max_concurrent_downloads=5,
        notification_duration=10,
        item_removal_delay=15,
        output_dir=Path("/custom/path"),
    )
    assert config.max_concurrent_downloads == 5
    assert config.notification_duration == 10
    assert config.item_removal_delay == 15
    assert config.output_dir == Path("/custom/path")


def test_validation_max_downloads_too_low():
    """Test validation catches too low max downloads."""
    with pytest.raises(ValueError, match="must be at least 1"):
        AppConfig(max_concurrent_downloads=0)


def test_validation_max_downloads_too_high():
    """Test validation catches too high max downloads."""
    with pytest.raises(ValueError, match="should not exceed 10"):
        AppConfig(max_concurrent_downloads=20)


def test_from_dict():
    """Test creating config from dictionary."""
    config_dict = {
        "max_concurrent_downloads": 4,
        "notification_duration": 7,
        "output_dir": "/tmp/downloads",
    }
    config = AppConfig.from_dict(config_dict)
    assert config.max_concurrent_downloads == 4
    assert config.notification_duration == 7
    assert config.output_dir == Path("/tmp/downloads")
```

### Manual Testing

1. **Launch application:**

   ```bash
   uv run humble sync
   ```

2. **Verify functionality:**

   - [x] App launches successfully
   - [x] Bundles load correctly
   - [x] Bundle details display properly
   - [x] Downloads work
   - [x] Status messages appear correctly
   - [x] Download counter displays correctly
   - [x] Items removed after delay

3. **Test configuration:**

   ```python
   # Test custom config
   from humble_tools.sync.app import HumbleBundleTUI
   from humble_tools.sync.config import AppConfig

   config = AppConfig(max_concurrent_downloads=5, notification_duration=10)
   app = HumbleBundleTUI(config=config)
   # Should use 5 max downloads and 10 second notifications
   ```

4. **Verify no regressions:**
   - [x] All keybindings work
   - [x] Format cycling works
   - [x] Concurrent downloads respect limit
   - [x] No new errors in logs

---

## Success Criteria Summary

### Code Quality

- [x] No magic numbers in app.py
- [x] All constants organized logically
- [x] Configuration properly validated
- [x] Type hints complete

### Functionality

- [x] All existing features work
- [x] No behavioral changes
- [x] Configuration can be customized
- [x] Default values match previous behavior

### Maintainability

- [x] Easy to find and update constants
- [x] Configuration documented
- [x] Ready for config file support
- [x] Clear separation of concerns

---

## Next Steps

After completing Phase 2:

1. **Verify all tests pass**
2. **Commit changes** with message: "Phase 2: Extract configuration and constants"
3. **Move to Phase 3:** Improve Readability (extract methods, simplify nesting)
4. **Consider:** Adding config file support in future enhancement

---

## Rollback Plan

If Phase 2 causes issues:

1. **Identify problem:**

   - Check logs for import errors
   - Verify constants are correct
   - Test with default config

2. **Quick fix:**

   - Revert to git commit before Phase 2
   - Or fix specific constant/config issue

3. **Verify rollback:**
   - Test application launches
   - Test downloads work
   - Check logs clean

---

## Appendix: Configuration File Format (Future)

For future reference, here's how a TOML config file might look:

```toml
# humble_config.toml

[download]
max_concurrent_downloads = 5
notification_duration = 10
item_removal_delay = 15

[paths]
output_dir = "~/Downloads/HumbleBundle"
session_file = "~/.config/humblebundle/session"

[display]
# Future: theme, colors, layout options
```

---

**Document Version:** 1.0  
**Last Updated:** December 22, 2025  
**Status:** Ready for Implementation
