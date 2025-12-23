# Phase 6: Comprehensive Documentation - Detailed Task Document

**Date Created:** December 23, 2025  
**Status:** Ready for Implementation  
**Priority:** MEDIUM  
**Estimated Effort:** 2-3 hours  
**Risk Level:** None (documentation only)  
**Dependencies:** Phases 1, 2, 3, 4, and 5 should be completed first

---

## Overview

Phase 6 focuses on creating comprehensive documentation for the Humble Tools project. This includes code-level documentation (docstrings, inline comments), architecture documentation, user guides, API references, and deployment documentation following MkDocs best practices.

### Goals

- ✅ Add comprehensive module-level docstrings with threading model explanation
- ✅ Document all classes with examples and usage patterns
- ✅ Add inline comments for complex logic and thread safety notes
- ✅ Create architecture overview documentation
- ✅ Document configuration system and options
- ✅ Create user guides for both CLI and TUI tools
- ✅ Add API reference documentation
- ✅ Create contributor's guide
- ✅ Set up MkDocs for static site generation

### Success Criteria

- [ ] All public modules have comprehensive docstrings
- [ ] All classes and methods documented with parameters and return types
- [ ] Complex logic sections have explanatory inline comments
- [ ] Threading model fully documented
- [ ] Configuration options documented with examples
- [ ] MkDocs site builds successfully
- [ ] Documentation passes linting (ruff)
- [ ] User can understand the project from documentation alone

---

## Prerequisites

⚠️ **RECOMMENDED:** Complete Phases 1-5 before Phase 6 for most accurate documentation:

**Why document after other phases?**

- Phase 4 adds DownloadQueue class that needs documentation
- Phase 5 adds error handling infrastructure requiring documentation
- Documentation will be more stable after code changes complete
- Reduces documentation rework

**However, Phase 6 can be done independently if needed.**

---

## Task 1: Add Comprehensive Module-Level Docstrings

**Priority:** HIGH  
**Estimated Time:** 45 minutes  
**Files:**

- `src/humble_tools/sync/app.py`
- `src/humble_tools/core/download_manager.py`
- `src/humble_tools/core/humble_wrapper.py`
- `src/humble_tools/core/tracker.py`
- `src/humble_tools/core/database.py`

### Problem

Current module docstrings are minimal or missing. They don't explain:

- Threading model and concurrency patterns
- Architecture and component relationships
- Usage examples
- Thread safety guarantees

### Solution

Add comprehensive module-level docstrings following Google/NumPy style with examples.

### Implementation

#### Step 1: Document app.py Threading Model

Edit `src/humble_tools/sync/app.py` to add comprehensive module docstring at the top:

````python
"""Textual-based TUI application for Humble Bundle library management.

This module provides an interactive terminal user interface for browsing and
downloading items from your Humble Bundle library. It uses the Textual framework
for the UI and integrates with humble-cli for API access.

Threading Model
===============

The application uses a hybrid threading model to keep the UI responsive:

**Main Thread (Event Loop)**
- All UI updates and reactive property changes
- Widget creation and screen management
- Event handling and keybindings
- Must use `call_from_thread()` when updating from worker threads

**Worker Threads (ThreadPoolExecutor)**
- I/O operations: bundle loading, downloads
- Decorated with `@work(thread=True)`
- Long-running operations that would block the UI
- Must acquire semaphore for concurrent downloads

Thread Safety
=============

**Download State Management**
- Download counters protected by `_download_lock`
- Semaphore limits concurrent downloads (configurable, default: 3)
- ItemFormatRow state modified only via `call_from_thread()`
- All widget queries must handle `NoMatches` (screen transitions)

**Concurrency Control**
- Max concurrent downloads: configurable via AppConfig
- Queue mechanism: semaphore + atomic counters
- Download states: not_started → queued → downloading → downloaded/failed
- Download completion removes item from UI after configurable delay

Architecture Overview
====================

The application consists of three main screens:

1. **BundleListScreen** - Browse available bundles
   - Loads bundle keys on mount
   - Displays bundle names in scrollable list
   - Sends BundleSelected message on selection

2. **BundleDetailsScreen** - View and download bundle items
   - Displays items with format availability
   - Shows download status indicators (✓ downloaded, 🕒 queued, ⏳ downloading)
   - Handles concurrent downloads with semaphore
   - Tracks download state in SQLite database

3. **GameKeysListScreen** - View game keys
   - Displays game keys with redemption status
   - Read-only view (redemption happens on Humble Bundle website)

State Management
================

**ItemFormatRow**
- Custom widget representing a downloadable item
- Reactive properties for download state (queued, downloading, downloaded)
- Format cycling via left/right arrow keys
- Automatic display updates via reactive watchers

**DownloadManager**
- Wraps humble-cli API and tracker database
- Provides format availability checking
- Handles actual file downloads
- Records downloads in SQLite database

Configuration
=============

Configuration is managed via `AppConfig` dataclass (see config.py):

- `max_concurrent_downloads`: Maximum simultaneous downloads (default: 3)
- `download_dir`: Output directory for downloads
- `notification_duration`: How long notifications display (default: 5s)
- `item_removal_delay`: Delay before removing completed items (default: 10s)
- Additional retry and error handling configuration (Phase 5)

Usage Example
=============

Basic usage:

```python
from pathlib import Path
from humble_tools.sync.app import HumbleBundleApp

# Create app with output directory
app = HumbleBundleApp(output_dir=Path("~/Downloads/HumbleBundle"))

# Run the TUI
app.run()
````

Custom configuration:

```python
from humble_tools.sync.config import AppConfig

config = AppConfig(
    max_concurrent_downloads=5,
    notification_duration=3.0,
)

app = HumbleBundleApp(
    output_dir=Path("~/Downloads"),
    config=config,
)
app.run()
```

# See Also

- `humble_tools.core.download_manager` - Download coordination
- `humble_tools.core.tracker` - Download history tracking
- `humble_tools.sync.config` - Configuration management
- Textual Documentation: https://textual.textualize.io/
  """

from pathlib import Path
from textual.app import App, ComposeResult

# ... rest of imports ...

````

#### Step 2: Document download_manager.py

Edit `src/humble_tools/core/download_manager.py`:

```python
"""Download management and coordination for Humble Bundle items.

This module provides the DownloadManager class which coordinates downloads
between the humble-cli API wrapper and the download tracker database.

Key Responsibilities
====================

1. **Format Availability** - Determine which formats are available for download
2. **URL Generation** - Generate download URLs for specific formats
3. **Download Execution** - Perform actual file downloads
4. **Progress Tracking** - Record downloads in SQLite database

Thread Safety
=============

DownloadManager is thread-safe for concurrent read operations but download
execution should be serialized per-file to avoid conflicts. The TUI application
handles this via semaphore-based concurrency control.

Usage Example
=============

Basic download workflow:

```python
from pathlib import Path
from humble_tools.core.download_manager import DownloadManager
from humble_tools.core.humble_wrapper import HumbleWrapper
from humble_tools.core.tracker import Tracker

# Initialize components
api = HumbleWrapper()
tracker = Tracker(db_path=Path("~/.humble-tools/tracker.db"))
manager = DownloadManager(humble_api=api, tracker=tracker)

# Get bundle details
bundle_data = api.get_bundle_details("your_bundle_key")

# Get first downloadable item
item = bundle_data["subproducts"][0]
download_data = item["downloads"][0]

# Check available formats
available_formats = manager.get_available_formats(download_data)
print(f"Available: {available_formats}")  # ['EPUB', 'PDF', 'MOBI']

# Get download URL for EPUB
epub_format = next(f for f in available_formats if f["name"] == "EPUB")
url = manager.get_format_download_url(epub_format, download_data)

# Download the file
success = manager.download_format(
    download_url=url,
    filename="book.epub",
    output_dir=Path("~/Downloads"),
)

if success:
    print("Download complete!")
````

# Error Handling (Phase 5)

When Phase 5 is implemented, download operations will raise custom exceptions:

- `NetworkError` - Transient network failures (retryable)
- `InsufficientStorageError` - Disk space issues
- `DownloadError` - General download failures
- See `humble_tools.core.exceptions` for full hierarchy

# See Also

- `humble_tools.core.humble_wrapper` - API wrapper
- `humble_tools.core.tracker` - Download tracking
- `humble_tools.core.exceptions` - Custom exceptions (Phase 5)
  """

from pathlib import Path
from typing import Any, Optional

# ... rest of imports ...

````

#### Step 3: Document Core Modules

Add similar comprehensive docstrings to:

**humble_wrapper.py:**
```python
"""Wrapper around humble-cli API with error translation.

Provides a clean interface to the Humble Bundle API via humble-cli,
with error translation to custom exceptions (Phase 5) and retry logic.

Key Features
============

- Authenticates via humble-cli session
- Fetches bundle keys and details
- Translates API errors to custom exceptions (Phase 5)
- Thread-safe for concurrent reads
...
"""
````

**tracker.py:**

```python
"""SQLite-based download tracking system.

Maintains a persistent record of downloaded files to prevent re-downloading.
Uses SHA-256 hashing of bundle_key + machine_name + filename as unique ID.

Database Schema
===============

Table: downloads
- id: TEXT PRIMARY KEY (SHA-256 hash)
- bundle_key: TEXT (bundle identifier)
- machine_name: TEXT (item machine name)
- filename: TEXT (downloaded filename)
- download_date: TIMESTAMP (when downloaded)
- file_size: INTEGER (bytes, optional)
- file_path: TEXT (full path, optional)

Thread Safety
=============

All database operations use WAL mode and are thread-safe. Concurrent
reads are allowed, writes are serialized by SQLite.
...
"""
```

**database.py:**

```python
"""Database connection management and migrations.

Provides a simple database manager for SQLite with:
- Automatic database creation
- Schema migrations
- Connection pooling (via SQLite WAL mode)
- Thread-safe operations

This is a minimal implementation focused on the download tracker's needs.
...
"""
```

**display.py:**

```python
"""Rich console formatting utilities for CLI output.

Provides formatted tables and displays for:
- Bundle lists with statistics
- Item details with format availability
- Game keys with redemption status
- Download progress

Uses the Rich library for colored, formatted console output.
...
"""
```

### Verification

- [ ] All module docstrings added
- [ ] Threading model explained in app.py
- [ ] Usage examples included
- [ ] No docstring linting errors (`ruff check`)

---

## Task 2: Document All Classes with Examples

**Priority:** HIGH  
**Estimated Time:** 45 minutes  
**Files:** All files with classes

### Problem

Class docstrings are missing or minimal. They don't include:

- Purpose and responsibilities
- Initialization parameters
- Usage examples
- Thread safety notes

### Solution

Add comprehensive class docstrings following Google/NumPy style.

### Implementation

#### Step 1: Document Main App Class

Edit `src/humble_tools/sync/app.py`:

````python
class HumbleBundleApp(App):
    """Interactive TUI application for Humble Bundle library management.

    This is the main application class that coordinates the TUI screens,
    manages global state, and handles navigation between bundle views.

    Attributes:
        CSS_PATH: Path to Textual CSS stylesheet
        SCREENS: Screen registry for Textual app
        BINDINGS: Global key bindings
        output_dir: Directory for downloaded files
        epub_manager: DownloadManager instance for API/tracker access
        config: Application configuration (AppConfig instance)

    Thread Safety:
        The app runs on Textual's event loop (main thread). All UI updates
        must happen on this thread. Worker threads must use call_from_thread().

    Example:
        Basic usage:

        ```python
        from pathlib import Path

        app = HumbleBundleApp(output_dir=Path("~/Downloads"))
        app.run()
        ```

        With custom configuration:

        ```python
        from humble_tools.sync.config import AppConfig

        config = AppConfig(max_concurrent_downloads=5)
        app = HumbleBundleApp(
            output_dir=Path("~/Downloads"),
            config=config,
        )
        app.run()
        ```

    See Also:
        - BundleListScreen: Main bundle listing screen
        - BundleDetailsScreen: Item download screen
        - GameKeysListScreen: Game keys display screen
    """
````

#### Step 2: Document Screen Classes

````python
class BundleListScreen(Screen):
    """Screen for displaying the list of available bundles.

    This screen loads all bundle keys from the Humble Bundle API and displays
    them in a scrollable list. Selecting a bundle navigates to the details screen.

    Attributes:
        epub_manager: DownloadManager for API access

    Key Bindings:
        - Enter: View selected bundle details
        - q: Quit application
        - ?: Show help

    Thread Safety:
        Bundle loading happens in a worker thread (@work(thread=True)).
        UI updates via call_from_thread() from the worker.

    State Management:
        No persistent state - reloads bundle list on each mount.

    Message Flow:
        Sends BundleSelected message when user selects a bundle.
        App intercepts message and pushes BundleDetailsScreen.

    Example Usage:
        This screen is automatically shown when the app starts.
        Not typically instantiated directly by user code.
    """


class BundleDetailsScreen(Screen):
    """Screen for viewing and downloading items from a bundle.

    This is the most complex screen, handling:
    - Item display with format indicators
    - Concurrent download management
    - Download state tracking
    - Format cycling (left/right arrows)
    - Game keys button (if bundle has keys)

    Attributes:
        epub_manager: DownloadManager for downloads
        output_dir: Download destination directory
        bundle_key: Current bundle identifier
        config: Application configuration

    Download Concurrency:
        Uses a semaphore to limit concurrent downloads (default: 3).
        Download states: queued → downloading → completed

    Format Selection:
        Each item shows available formats (EPUB, PDF, MOBI).
        User cycles through formats with arrow keys before downloading.
        Selected format shown in bold cyan.

    Status Indicators:
        - ✓ (green): Downloaded
        - 🕒 (blue): Queued
        - ⏳ (yellow): Downloading
        - No indicator: Not downloaded

    Key Bindings:
        - Enter: Download selected format for item
        - Left/Right: Cycle format selection
        - Escape: Back to bundle list
        - k: View game keys (if available)

    Thread Safety:
        Downloads run in worker threads. All ItemFormatRow updates
        via call_from_thread(). Download counters protected by _download_lock.

    Example:
        Typically navigated to via BundleListScreen, not created directly.
    """


class ItemFormatRow(Static):
    """Widget representing a downloadable item with format selection.

    This custom widget displays:
    - Item number and name
    - Available formats (EPUB, PDF, MOBI, etc.)
    - Download status per format
    - Item size

    The widget uses Textual's reactive system to automatically update
    the display when download states change.

    Attributes:
        item_number: Numeric position in bundle
        item_name: Item display name
        formats: Available format names (list)
        item_size: Human-readable size string
        download_data: Raw API data for downloads
        format_status: Dict mapping format to downloaded status
        format_queued: Dict mapping format to queued status
        format_downloading: Dict mapping format to downloading status
        selected_format: Currently selected format name

    Reactive Properties:
        All *_status dicts are reactive - changes trigger display rebuild.
        This ensures the UI stays in sync with download state.

    Thread Safety:
        State changes must happen via call_from_thread() from workers.
        The reactive system handles thread-safe UI updates.

    Example:
        ```python
        # Create item row
        item_row = ItemFormatRow(
            item_number=1,
            item_name="Example Book",
            formats=["EPUB", "PDF"],
            item_size="25.3 MB",
            download_data=api_download_data,
            format_status={"EPUB": True, "PDF": False},
        )

        # Update download status (from worker thread)
        app.call_from_thread(
            lambda: setattr(item_row.format_downloading, "EPUB", True)
        )
        ```

    See Also:
        BundleDetailsScreen: Parent screen that creates ItemFormatRow instances
    """
````

#### Step 3: Document Configuration Classes

Edit `src/humble_tools/sync/config.py`:

````python
@dataclass(frozen=True)
class AppConfig:
    """Application configuration with validation.

    Immutable configuration object for the TUI application. All settings
    have sensible defaults and are validated on construction.

    Attributes:
        max_concurrent_downloads: Maximum simultaneous downloads (default: 3)
            Must be >= 1. Controls semaphore size.

        notification_duration: Notification display time in seconds (default: 5.0)
            Must be > 0. How long success/error messages show.

        item_removal_delay: Delay before removing completed items in seconds (default: 10.0)
            Must be >= 0. Time before downloaded items disappear from list.

        max_item_name_length: Maximum characters for item name display (default: 50)
            Must be > 0. Longer names are truncated with "...".

        format_display_width: Width of format column in characters (default: 30)
            Must be > 0. Controls layout of format indicators.

    Validation:
        All parameters validated in __post_init__. Raises ValueError for
        invalid configuration values.

    Example:
        Default configuration:

        ```python
        config = AppConfig()
        ```

        Custom configuration:

        ```python
        config = AppConfig(
            max_concurrent_downloads=5,
            notification_duration=3.0,
            item_removal_delay=5.0,
        )
        ```

        Invalid configuration (raises ValueError):

        ```python
        config = AppConfig(max_concurrent_downloads=0)  # Must be >= 1
        ```

    See Also:
        - constants.py: Global constants used as defaults
        - HumbleBundleApp: Main app that accepts AppConfig
    """
````

### Verification

- [ ] All classes documented
- [ ] Examples included
- [ ] Thread safety notes added
- [ ] Attributes documented
- [ ] No docstring linting errors

---

## Task 3: Add Inline Comments for Complex Logic

**Priority:** MEDIUM  
**Estimated Time:** 30 minutes  
**Files:** `src/humble_tools/sync/app.py`

### Problem

Complex logic sections lack explanatory comments:

- Download state management
- Semaphore acquisition/release
- Format indicator logic
- Thread synchronization

### Solution

Add focused inline comments explaining WHY, not WHAT.

### Implementation

#### Step 1: Document Download Method

Edit the `download_format` method in `BundleDetailsScreen`:

```python
@work(thread=True)
def download_format(self, item_row: ItemFormatRow) -> None:
    """Download the selected format for an item."""
    selected_format = item_row.selected_format

    # Skip if already downloaded/queued/downloading
    if item_row.format_status.get(selected_format, False):
        return
    if item_row.format_queued.get(selected_format, False):
        return
    if item_row.format_downloading.get(selected_format, False):
        return

    # Track whether we successfully acquired the semaphore
    # Important: only release if we acquired it
    semaphore_acquired = False

    # ... rest of implementation with comments at key points ...

    try:
        # Block until download slot available
        # This prevents overwhelming the network or API rate limits
        self._download_semaphore.acquire()
        semaphore_acquired = True

        # Update UI: move from queued to downloading
        # Must use call_from_thread since we're in a worker thread
        self.app.call_from_thread(start_downloading)

        # Perform actual download
        # This may take several seconds to minutes depending on file size
        success = self.epub_manager.download_format(...)

        if success:
            # Record success in tracker database and update UI
            self.app.call_from_thread(on_success)
        else:
            # Download failed without exception (e.g., HTTP 404)
            self.app.call_from_thread(lambda: on_failure(error_msg))

    except NetworkError as e:
        # Network errors are retryable (Phase 5)
        # RetryManager already attempted retries before reaching here
        # Show user-friendly message and record error
        ...

    finally:
        # Critical: only release semaphore if we acquired it
        # Prevents semaphore corruption if acquire() raised exception
        if semaphore_acquired:
            with self._download_lock:
                # Atomically decrement active counter
                # Lock prevents race with other downloads completing
                self._active_downloads -= 1

            # Release download slot for next queued item
            self._download_semaphore.release()

            # Update status display
            self.app.call_from_thread(self._update_download_status)
```

#### Step 2: Document Format Indicator Logic

```python
def _get_status_indicator(self, fmt: str) -> tuple[str, str | None]:
    """Determine status indicator and color for a format.

    Priority order (highest to lowest):
    1. Queued (🕒 blue) - waiting for download slot
    2. Downloading (⏳ yellow) - actively downloading
    3. Downloaded (✓ green) - present in tracker DB
    4. Not started (space, no color) - available to download

    This priority ensures UI shows the most current state when
    multiple state transitions happen rapidly.
    """
    if self.format_queued.get(fmt, False):
        return "🕒", "blue"
    elif self.format_downloading.get(fmt, False):
        return "⏳", "yellow"
    elif self.format_status.get(fmt, False):
        return "✓", "green"
    else:
        return " ", None
```

#### Step 3: Document Thread Synchronization

```python
def _update_download_status(self) -> None:
    """Update download status display in footer.

    This method must be called from the main thread (event loop).
    Worker threads must use: self.app.call_from_thread(self._update_download_status)

    Thread Safety:
        Reads from _active_downloads and _queued_downloads which are
        protected by _download_lock. Creates snapshot of values to
        avoid holding lock during UI update.
    """
    # Take snapshot while holding lock to ensure consistency
    with self._download_lock:
        active = self._active_downloads
        queued = self._queued_downloads

    # Update UI (lock not needed for UI operations)
    status_text = f"Downloads: {active} active, {queued} queued"
    try:
        self.query_one("#details-status", Static).update(status_text)
    except NoMatches:
        # Screen may have transitioned - ignore
        pass
```

### Verification

- [ ] Complex sections commented
- [ ] Thread safety notes added
- [ ] WHY explained, not just WHAT
- [ ] Comments don't state obvious

---

## Task 4: Create MkDocs Documentation Site

**Priority:** HIGH  
**Estimated Time:** 60 minutes  
**Files:** `docs/` directory (new), `mkdocs.yml` (new)

### Problem

No user-facing documentation site. Users need:

- Installation guide
- Usage tutorials
- Architecture overview
- API reference
- Configuration reference
- Troubleshooting guide

### Solution

Set up MkDocs with Material theme for comprehensive documentation site.

### Implementation

#### Step 1: Install MkDocs Dependencies

Add to `pyproject.toml`:

```toml
[project.optional-dependencies]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.5.0",
    "mkdocstrings[python]>=0.24.0",
    "mkdocs-gen-files>=0.5.0",
]
```

Install:

```bash
uv pip install -e ".[docs]"
```

#### Step 2: Create MkDocs Configuration

Create `mkdocs.yml` in project root:

```yaml
site_name: Humble Tools
site_description: Interactive TUI and CLI tools for Humble Bundle library management
site_author: Your Name
site_url: https://yourusername.github.io/humblebundle

repo_name: yourusername/humblebundle
repo_url: https://github.com/yourusername/humblebundle
edit_uri: edit/main/docs/

theme:
  name: material
  palette:
    # Light mode
    - scheme: default
      primary: deep purple
      accent: purple
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    # Dark mode
    - scheme: slate
      primary: deep purple
      accent: purple
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy
    - content.code.annotate

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true
            show_category_heading: true
            members_order: source
            separate_signature: true
            show_signature_annotations: true

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.tabbed:
      alternate_style: true
  - tables
  - attr_list
  - md_in_html
  - toc:
      permalink: true

nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - Quick Start: getting-started/quickstart.md
      - Authentication: getting-started/authentication.md
  - User Guide:
      - humble-sync (TUI): user-guide/tui.md
      - humble-track (CLI): user-guide/cli.md
      - Configuration: user-guide/configuration.md
      - Keyboard Shortcuts: user-guide/shortcuts.md
  - Architecture:
      - Overview: architecture/overview.md
      - Threading Model: architecture/threading.md
      - Download Management: architecture/downloads.md
      - Database Schema: architecture/database.md
  - API Reference:
      - App: api/app.md
      - Download Manager: api/download_manager.md
      - Tracker: api/tracker.md
      - Configuration: api/config.md
  - Development:
      - Contributing: development/contributing.md
      - Testing: development/testing.md
      - Code Style: development/style.md
  - Troubleshooting: troubleshooting.md
  - Changelog: changelog.md

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/yourusername/humblebundle
```

#### Step 3: Create Documentation Structure

Create directory structure:

```bash
mkdir -p docs/{getting-started,user-guide,architecture,api,development}
```

#### Step 4: Create Main Documentation Files

**docs/index.md:**

```markdown
# Humble Tools

Two complementary tools for managing your Humble Bundle library, built on top of `humble-cli`.

## Features

:material-monitor: **Interactive TUI** - Full-screen terminal UI for browsing and downloading

:material-download: **Progress Tracking** - Visual statistics and download history

:material-check-all: **Format Support** - EPUB, PDF, MOBI with format cycling

:material-key: **Game Keys** - View game key names and redemption status

:material-cog: **Configurable** - Customize concurrent downloads, paths, and behavior

## Quick Links

- [Installation](getting-started/installation.md)
- [Quick Start Guide](getting-started/quickstart.md)
- [TUI User Guide](user-guide/tui.md)
- [CLI User Guide](user-guide/cli.md)

## Overview

### humble-sync (Interactive TUI)

Browse your entire Humble Bundle library in an interactive terminal interface:

- Navigate bundles with keyboard
- View all items with format availability
- Download with visual progress indicators
- Automatic duplicate prevention
- Format cycling before download

### humble-track (CLI Tool)

Command-line interface for download tracking and statistics:

- Mark files as downloaded manually
- View download progress per bundle
- Show bundle statistics
- Query download history

## Why These Tools?

While `humble-cli` handles authentication and downloads, Humble Tools adds:

- **Visual Interface** - No command typing for every action
- **Status Tracking** - Know what's already downloaded
- **Concurrent Downloads** - Multiple downloads simultaneously
- **Format Management** - Choose format before downloading
- **Progress Monitoring** - See statistics across all bundles

## Requirements

- Python 3.8 or higher
- [humble-cli](https://github.com/smbl64/humble-cli) installed and authenticated

See [Installation](getting-started/installation.md) for detailed setup instructions.
```

**docs/getting-started/installation.md:**

````markdown
# Installation

## Prerequisites

### Python

Humble Tools requires Python 3.8 or higher:

```bash
python --version  # Should be 3.8+
```
````

### humble-cli

Install [humble-cli](https://github.com/smbl64/humble-cli) by [@smbl64](https://github.com/smbl64):

**Option 1: Pre-built binaries (Recommended)**

Download from [releases page](https://github.com/smbl64/humble-cli/releases) for your platform.

**Option 2: Via Cargo**

```bash
cargo install humble-cli
```

**Verify installation:**

```bash
humble-cli --version
```

## Install Humble Tools

### Using uv (Recommended)

```bash
# Install as a tool
uv tool install git+https://github.com/yourusername/humblebundle

# Or install from local directory
uv tool install .
```

### Using pip

```bash
pip install git+https://github.com/yourusername/humblebundle

# Or from local directory
pip install .
```

### From Source

```bash
# Clone repository
git clone https://github.com/yourusername/humblebundle
cd humblebundle

# Install with uv
uv sync

# Or with pip
pip install -e .
```

## Verify Installation

```bash
# Check TUI tool
humble-sync --help

# Check CLI tool
humble-track --help
```

## Next Steps

- [Authentication](authentication.md) - Set up Humble Bundle access
- [Quick Start](quickstart.md) - First steps with the tools

````

**docs/getting-started/quickstart.md:**

```markdown
# Quick Start

Get started with Humble Tools in 5 minutes.

## 1. Authenticate

First, get your session key from Humble Bundle:

1. Log into [Humble Bundle](https://www.humblebundle.com) in your browser
2. Open browser developer tools (F12)
3. Go to Application/Storage → Cookies
4. Find the `_simpleauth_sess` cookie and copy its value

Then authenticate:

```bash
humble-cli auth "YOUR_SESSION_KEY"
````

## 2. Launch TUI

Start the interactive terminal UI:

```bash
humble-sync
```

You'll see your bundle list load automatically.

## 3. Navigate and Download

**Browse Bundles:**

- ↑↓ - Navigate bundle list
- Enter - Open bundle details
- Esc - Go back

**Download Items:**

- ↑↓ - Select item
- ←→ - Cycle through formats (EPUB, PDF, MOBI)
- Enter - Download selected format
- k - View game keys (if available)

**Status Indicators:**

- ✓ (green) - Already downloaded
- 🕒 (blue) - Queued for download
- ⏳ (yellow) - Downloading now

## 4. Track Progress (CLI)

Check download statistics:

```bash
# Show all bundles with stats
humble-track list

# Show specific bundle details
humble-track show BUNDLE_KEY

# Manually mark a file as downloaded
humble-track mark BUNDLE_KEY MACHINE_NAME FILENAME
```

## What's Next?

- [Full TUI Guide](../user-guide/tui.md) - All features and shortcuts
- [CLI Reference](../user-guide/cli.md) - Command-line usage
- [Configuration](../user-guide/configuration.md) - Customize behavior

````

**docs/architecture/overview.md:**

```markdown
# Architecture Overview

Humble Tools consists of two main applications sharing common infrastructure.

## Component Architecture

````

┌─────────────────────────────────────────┐
│ User Interface Layer │
├─────────────────┬───────────────────────┤
│ humble-sync │ humble-track │
│ (Textual TUI) │ (Rich CLI) │
└─────────────────┴───────────────────────┘
│ │
└───────┬───────────┘
↓
┌─────────────────────────────────────────┐
│ Business Logic Layer │
├──────────────────┬──────────────────────┤
│ DownloadManager │ Display Formatters │
└──────────────────┴──────────────────────┘
│
↓
┌─────────────────────────────────────────┐
│ Data Access Layer │
├──────────────────┬──────────────────────┤
│ HumbleWrapper │ Tracker │
│ (API Access) │ (SQLite Database) │
└──────────────────┴──────────────────────┘
│ │
↓ ↓
┌──────────────────┐ ┌─────────────────┐
│ humble-cli │ │ tracker.db │
│ (External) │ │ (SQLite) │
└──────────────────┘ └─────────────────┘

```

## Core Components

### DownloadManager

Central coordinator for download operations:

- Wraps HumbleWrapper and Tracker
- Determines format availability
- Generates download URLs
- Executes downloads
- Records history

See [Download Management](downloads.md) for details.

### HumbleWrapper

API wrapper around humble-cli:

- Authenticates via humble-cli session
- Fetches bundle keys and details
- Provides clean Python interface
- Handles error translation (Phase 5)

### Tracker

SQLite-based download tracking:

- Prevents re-downloading
- Records download history
- Provides query interface
- Thread-safe operations

See [Database Schema](database.md) for details.

### Display Formatters

Rich console formatting:

- Bundle lists with statistics
- Item tables with formats
- Game keys with status
- Progress indicators

## Threading Model

See [Threading Model](threading.md) for detailed explanation of:

- Main thread (event loop)
- Worker threads (I/O operations)
- Concurrency control
- Thread safety guarantees

## Data Flow

**Bundle Loading:**

```

User → Screen → HumbleWrapper → humble-cli → API → Response

```

**Download Operation:**

```

User → ItemFormatRow → BundleDetailsScreen
→ DownloadManager → humble-cli → File Download
→ Tracker → Database Record
→ UI Update

```

## Error Handling (Phase 5)

Custom exception hierarchy for:

- Network errors (retryable)
- Authentication failures
- API errors
- Download errors
- Configuration errors

See error handling documentation for details.
```

**docs/architecture/threading.md:**

````markdown
# Threading Model

The TUI application uses a hybrid threading model to keep the UI responsive while performing blocking I/O operations.

## Overview

### Main Thread (Event Loop)

**Purpose:** UI rendering and event handling

**Runs on:**

- Textual event loop
- Single-threaded
- Handles all UI updates

**Responsibilities:**

- Widget rendering
- Event dispatching
- Reactive property updates
- Screen management
- User input handling

### Worker Threads (ThreadPoolExecutor)

**Purpose:** Blocking I/O operations

**Runs on:**

- Thread pool managed by Textual
- Multiple threads
- Controlled by `@work(thread=True)` decorator

**Responsibilities:**

- Bundle loading from API
- File downloads
- Database operations
- Network requests

## Thread Communication

### call_from_thread()

Worker threads cannot directly update UI. They must use:

```python
# In worker thread
@work(thread=True)
def load_bundles(self) -> None:
    bundles = api.get_bundles()  # Blocking I/O

    # Update UI from worker thread
    self.app.call_from_thread(
        lambda: self.update_bundle_list(bundles)
    )
```
````

### Why This Pattern?

Textual's UI framework is not thread-safe. All UI operations must happen on the main event loop.

## Concurrency Control

### Download Semaphore

Limits concurrent downloads:

```python
# Initialize with max concurrent count
self._download_semaphore = threading.Semaphore(3)

# Acquire before download
self._download_semaphore.acquire()
try:
    download_file()
finally:
    self._download_semaphore.release()
```

### Download Counters

Track active and queued downloads:

```python
# Protected by lock for thread safety
self._download_lock = threading.Lock()
self._active_downloads = 0
self._queued_downloads = 0

# Atomic operations
with self._download_lock:
    self._active_downloads += 1
```

## Thread Safety Guarantees

### Thread-Safe Components

✅ **Tracker (Database)** - SQLite WAL mode allows concurrent reads  
✅ **HumbleWrapper** - Read-only operations safe  
✅ **DownloadManager** - Stateless, safe for concurrent use  
✅ **Download Counters** - Protected by locks

### Not Thread-Safe

❌ **ItemFormatRow** - Must update via `call_from_thread()`  
❌ **Screen Widgets** - UI operations main thread only  
❌ **Reactive Properties** - Set via main thread only

## Common Patterns

### Pattern 1: Loading Data

```python
@work(thread=True)
def load_data(self) -> None:
    # Worker thread - safe for I/O
    data = blocking_api_call()

    # Update UI - must use call_from_thread
    self.app.call_from_thread(
        lambda: self.display_data(data)
    )
```

### Pattern 2: Download with Status

```python
@work(thread=True)
def download(self, item_row: ItemFormatRow) -> None:
    # Acquire semaphore
    self._download_semaphore.acquire()
    acquired = True

    try:
        # Update UI: downloading
        self.app.call_from_thread(
            lambda: setattr(item_row.format_downloading, fmt, True)
        )

        # Perform download (blocking)
        success = download_file()

        # Update UI: complete
        if success:
            self.app.call_from_thread(
                lambda: setattr(item_row.format_status, fmt, True)
            )
    finally:
        if acquired:
            self._download_semaphore.release()
```

### Pattern 3: Safe Widget Query

```python
def update_status(self, message: str) -> None:
    """Update status widget (call from main thread)."""
    try:
        widget = self.query_one("#status", Static)
        widget.update(message)
    except NoMatches:
        # Screen transitioned - ignore
        pass
```

## Performance Considerations

### Thread Pool Size

Textual manages the thread pool automatically. Default size is typically 10 threads, sufficient for most workloads.

### Download Concurrency

Default: 3 concurrent downloads

**Too Low:**

- Underutilizes network
- Slow for small files

**Too High:**

- Overwhelms API rate limits
- High memory usage
- Connection errors

**Configurable via AppConfig:**

```python
config = AppConfig(max_concurrent_downloads=5)
```

## Debugging Thread Issues

### Enable Thread Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

**Issue:** UI doesn't update from worker

**Cause:** Forgot `call_from_thread()`

**Solution:** Wrap all UI updates:

```python
self.app.call_from_thread(lambda: update_ui())
```

---

**Issue:** Semaphore count incorrect

**Cause:** Release without acquire (exception path)

**Solution:** Track acquisition state:

```python
acquired = False
try:
    sem.acquire()
    acquired = True
    ...
finally:
    if acquired:
        sem.release()
```

---

**Issue:** Race condition in counters

**Cause:** Missing lock protection

**Solution:** Use lock for all counter access:

```python
with self._download_lock:
    self._active_downloads += 1
```

````

#### Step 5: Generate API Reference

Create `docs/api/app.md`:

```markdown
# App Module

::: humble_tools.sync.app
    options:
      show_root_heading: true
      show_source: true
      members:
        - HumbleBundleApp
        - BundleListScreen
        - BundleDetailsScreen
        - ItemFormatRow
        - GameKeysListScreen
````

Similar files for other modules: `download_manager.md`, `tracker.md`, `config.md`.

#### Step 6: Build and Test

```bash
# Build documentation
mkdocs build

# Serve locally
mkdocs serve

# Open browser to http://127.0.0.1:8000
```

### Verification

- [ ] MkDocs builds without errors
- [ ] All pages render correctly
- [ ] Navigation works
- [ ] Code blocks syntax highlighted
- [ ] API reference generated
- [ ] Search works

---

## Task 5: Create Contributing Guide

**Priority:** MEDIUM  
**Estimated Time:** 20 minutes  
**File:** `docs/development/contributing.md`

### Implementation

Create `docs/development/contributing.md`:

````markdown
# Contributing Guide

Thank you for considering contributing to Humble Tools!

## Development Setup

### Prerequisites

- Python 3.8+
- uv (recommended) or pip
- Git

### Clone and Install

```bash
# Clone repository
git clone https://github.com/yourusername/humblebundle
cd humblebundle

# Create virtual environment and install dependencies
uv sync

# Install pre-commit hooks
pre-commit install
```
````

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/my-feature
```

### 2. Make Changes

Edit code following our [Code Style](style.md) guidelines.

### 3. Run Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_config.py

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### 4. Format and Lint

```bash
# Format code
uv run ruff format src tests

# Fix linting issues
uv run ruff check src tests --fix

# Type check
uv run mypy src
```

### 5. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add feature: description"
```

Pre-commit hooks will run automatically:

- ruff format
- ruff check
- gitleaks (secret detection)

### 6. Push and Create PR

```bash
git push origin feature/my-feature
```

Then create a Pull Request on GitHub.

## Testing Guidelines

### Unit Tests

- Test single functions/methods in isolation
- Mock external dependencies
- Fast execution (< 1s per test)
- Located in `tests/unit/`

Example:

```python
def test_config_validation():
    """Test AppConfig validates max_concurrent_downloads."""
    with pytest.raises(ValueError):
        AppConfig(max_concurrent_downloads=0)
```

### Integration Tests

- Test component interactions
- Use real dependencies where practical
- Mock only external APIs
- Located in `tests/integration/`

Example:

```python
async def test_bundle_navigation(app):
    """Test navigating from bundle list to details."""
    async with app.run_test() as pilot:
        await pilot.press("enter")
        assert isinstance(app.screen, BundleDetailsScreen)
```

## Code Style

### Python Style

We follow PEP 8 with these tools:

- **ruff**: Formatting and linting
- **mypy**: Type checking

### Type Hints

Always use type hints:

```python
def download_format(
    self,
    download_url: str,
    filename: str,
    output_dir: Path,
) -> bool:
    """Download a file to the specified directory."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_size(bytes: int) -> str:
    """Convert bytes to human-readable size string.

    Args:
        bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")

    Example:
        >>> calculate_size(1536000)
        '1.5 MB'
    """
    ...
```

### Imports

Order imports:

1. Standard library
2. Third-party packages
3. Local modules

```python
# Standard library
from pathlib import Path
from typing import Optional

# Third-party
from textual.app import App
from rich.console import Console

# Local
from humble_tools.core.tracker import Tracker
```

## Project Structure

Understanding the codebase:

```
src/humble_tools/
├── core/              # Business logic
│   ├── database.py    # Database management
│   ├── download_manager.py  # Download coordination
│   ├── humble_wrapper.py    # API wrapper
│   ├── tracker.py     # Download tracking
│   └── display.py     # Console formatting
├── sync/              # TUI application
│   ├── app.py         # Main TUI app
│   ├── config.py      # Configuration
│   └── constants.py   # Constants
└── track/             # CLI application
    └── commands.py    # CLI commands

tests/
├── unit/              # Unit tests
└── integration/       # Integration tests
```

## Getting Help

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing issues before creating new ones

## Code Review

All contributions go through code review. Reviewers check for:

- Code correctness
- Test coverage
- Documentation
- Code style compliance
- Type safety

Be patient and responsive to feedback!

````

### Verification

- [ ] Contributing guide complete
- [ ] Development setup clear
- [ ] Workflow explained
- [ ] Code style documented

---

## Task 6: Add Configuration Documentation

**Priority:** MEDIUM
**Estimated Time:** 15 minutes
**File:** `docs/user-guide/configuration.md`

### Implementation

Create `docs/user-guide/configuration.md`:

```markdown
# Configuration

Humble Tools can be customized through the `AppConfig` class.

## Configuration Options

### Download Behavior

**max_concurrent_downloads** (default: `3`)

Maximum number of simultaneous downloads.

- Range: 1-10
- Higher values: faster for small files, risk rate limiting
- Lower values: conservative, reliable

```python
from humble_tools.sync.config import AppConfig

config = AppConfig(max_concurrent_downloads=5)
````

### UI Behavior

**notification_duration** (default: `5.0`)

How long notifications display (seconds).

```python
config = AppConfig(notification_duration=3.0)
```

**item_removal_delay** (default: `10.0`)

Delay before completed items disappear (seconds).

```python
config = AppConfig(item_removal_delay=15.0)
```

### Display Settings

**max_item_name_length** (default: `50`)

Maximum characters for item names before truncation.

```python
config = AppConfig(max_item_name_length=60)
```

**format_display_width** (default: `30`)

Width of format column in characters.

```python
config = AppConfig(format_display_width=40)
```

## Using Custom Configuration

### Option 1: Programmatic

```python
from pathlib import Path
from humble_tools.sync.app import HumbleBundleApp
from humble_tools.sync.config import AppConfig

# Create custom config
config = AppConfig(
    max_concurrent_downloads=5,
    notification_duration=3.0,
    item_removal_delay=5.0,
)

# Pass to app
app = HumbleBundleApp(
    output_dir=Path("~/Downloads"),
    config=config,
)

app.run()
```

### Option 2: Environment Variables (Future)

_Environment variable support planned for future release._

## Configuration Validation

Invalid configuration raises `ValueError`:

```python
# This will raise ValueError
config = AppConfig(max_concurrent_downloads=0)
# Error: max_concurrent_downloads must be at least 1

# This will raise ValueError
config = AppConfig(notification_duration=-1)
# Error: notification_duration must be positive
```

## Advanced Configuration

### Retry Configuration (Phase 5)

When Phase 5 is implemented:

```python
config = AppConfig(
    max_retry_attempts=3,
    retry_base_delay=1.0,
    retry_max_delay=30.0,
)
```

### Database Location

Currently defaults to `~/.humble-tools/tracker.db`.

Custom database location (future feature):

```python
from humble_tools.core.tracker import Tracker

tracker = Tracker(db_path=Path("/custom/path/tracker.db"))
```

## Best Practices

### Conservative Defaults

Use default configuration unless you have specific needs. Defaults are tested and reliable.

### Network Limits

If experiencing rate limiting or connection errors, reduce `max_concurrent_downloads`.

### Display Tuning

Adjust `max_item_name_length` and `format_display_width` for your terminal width.

### Testing Configuration

Always test configuration changes with a small bundle first:

```python
# Test with conservative settings
config = AppConfig(max_concurrent_downloads=1)
app = HumbleBundleApp(output_dir=test_path, config=config)
```

## Configuration Reference

| Option                     | Type  | Default | Range | Description                      |
| -------------------------- | ----- | ------- | ----- | -------------------------------- |
| `max_concurrent_downloads` | int   | 3       | 1-10  | Simultaneous downloads           |
| `notification_duration`    | float | 5.0     | > 0   | Notification display time (s)    |
| `item_removal_delay`       | float | 10.0    | >= 0  | Completed item removal delay (s) |
| `max_item_name_length`     | int   | 50      | > 0   | Max characters for item names    |
| `format_display_width`     | int   | 30      | > 0   | Format column width              |

## See Also

- [API Reference: Config](../api/config.md) - Full API documentation
- [Architecture Overview](../architecture/overview.md) - How configuration is used

````

### Verification

- [ ] All options documented
- [ ] Examples provided
- [ ] Validation explained
- [ ] Best practices included

---

## Verification Checklist

### Code Documentation

- [ ] All modules have comprehensive docstrings
- [ ] All classes documented with examples
- [ ] Complex logic has inline comments
- [ ] Threading model fully documented
- [ ] No docstring linting errors

### MkDocs Site

- [ ] Site builds without errors
- [ ] All pages render correctly
- [ ] Navigation works
- [ ] Search functional
- [ ] API reference generated
- [ ] Mobile-responsive

### Content Quality

- [ ] Installation guide complete
- [ ] Quick start guide works
- [ ] User guides comprehensive
- [ ] Architecture explained
- [ ] Configuration documented
- [ ] Contributing guide clear

### Technical

- [ ] Links not broken
- [ ] Code examples valid
- [ ] Images display (if any)
- [ ] Syntax highlighting works
- [ ] Table formatting correct

---

## Deployment

### GitHub Pages

#### Option 1: GitHub Actions (Recommended)

Create `.github/workflows/docs.yml`:

```yaml
name: Deploy Documentation

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install mkdocs-material mkdocstrings[python]

      - name: Build documentation
        run: mkdocs build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: site/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
````

Enable GitHub Pages in repository settings (Source: GitHub Actions).

#### Option 2: Manual Deployment

```bash
# Build and deploy
mkdocs gh-deploy

# Or build locally and push
mkdocs build
# Copy site/ directory to GitHub Pages branch
```

### Custom Domain (Optional)

1. Add `CNAME` file to `docs/`:

   ```
   docs.yourdomain.com
   ```

2. Add to `mkdocs.yml`:

   ```yaml
   site_url: https://docs.yourdomain.com
   ```

3. Configure DNS:
   ```
   CNAME docs.yourdomain.com -> yourusername.github.io
   ```

---

## Maintenance

### Updating Documentation

Documentation should be updated when:

- [ ] New features added
- [ ] APIs change
- [ ] Configuration options added
- [ ] Architecture evolves
- [ ] Bugs affect documented behavior

### Documentation Review

Regular review checklist:

- [ ] Examples still work
- [ ] Links not broken
- [ ] Screenshots current (if any)
- [ ] Version numbers accurate
- [ ] Dependencies up to date

### Feedback Integration

Monitor and address:

- GitHub issues about documentation
- User questions revealing gaps
- Confusion patterns
- Feature requests

---

## Success Metrics

### Quantitative

- **Build Time:** < 30 seconds
- **Page Load:** < 2 seconds
- **Search Results:** < 1 second
- **Coverage:** 100% of public APIs documented

### Qualitative

- **Clarity:** New users can start without external help
- **Completeness:** All features explained
- **Accuracy:** Examples work as shown
- **Maintainability:** Easy to update

---

## Future Enhancements

### Content

- Video tutorials
- Interactive examples
- FAQ section
- Troubleshooting flowcharts
- Performance tuning guide

### Technical

- Version dropdown (multiple versions)
- PDF export
- Offline documentation
- Translation support (i18n)
- Analytics integration

### Community

- Blog section for updates
- Community showcase
- Plugin/extension documentation
- Integration examples

---

## Appendix: MkDocs Commands

### Common Commands

```bash
# Create new site
mkdocs new .

# Serve locally with live reload
mkdocs serve

# Build static site
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy

# Clean build directory
rm -rf site/
```

### Development Server

```bash
# Serve on custom port
mkdocs serve --dev-addr=127.0.0.1:8080

# Serve on all interfaces
mkdocs serve --dev-addr=0.0.0.0:8000
```

### Build Options

```bash
# Build with strict mode (fail on warnings)
mkdocs build --strict

# Build with verbose output
mkdocs build --verbose

# Clean before build
mkdocs build --clean
```

---

## Appendix: Documentation Style Guide

### Writing Style

- **Active voice:** "Click the button" not "The button should be clicked"
- **Present tense:** "The app downloads files" not "The app will download files"
- **Second person:** "You can configure" not "One can configure"
- **Concise:** Remove unnecessary words
- **Specific:** "3 seconds" not "a few seconds"

### Code Examples

- Always test examples before documenting
- Include imports in examples
- Show expected output
- Add comments for complex logic
- Use realistic data

### Structure

- Start with overview/purpose
- Add prerequisites if needed
- Show basic example first
- Progress to advanced examples
- Include troubleshooting

### Links

- Use relative links for internal pages
- Use descriptive link text ("see installation guide" not "click here")
- Add external link icons for external sites
- Keep links up to date

---

**Document Version:** 1.0  
**Author:** GitHub Copilot  
**Last Updated:** December 23, 2025  
**Status:** Ready for Implementation
