# Humble Bundle EPUB Manager - Implementation Documentation

## Overview

The Humble Bundle EPUB Manager is an interactive TUI and download tracking tool for managing your Humble Bundle library. It is built on top of `humble-cli` and focuses on providing value through visual interfaces and persistent download tracking, rather than duplicating existing CLI functionality.

### Architectural Decision: Focused Scope

This tool intentionally **does not duplicate** `humble-cli` functionality. The philosophy is:

- **humble-cli** handles: Authentication, bundle listing, searching, and downloading
- **hb-epub** adds: Interactive TUI, download tracking, visual progress indicators, and formatted displays

By avoiding feature duplication, the tool:

- Remains lightweight and maintainable
- Clearly complements rather than replaces humble-cli
- Focuses development effort on unique value-add features
- Reduces testing surface and potential for inconsistencies

Users are expected to use `humble-cli` directly for most operations, and use `hb-epub` for browsing, tracking, and visualizing their library.

## Architecture

### Core Components

The application is organized into several modules, each with specific responsibilities:

```
src/humblebundle_epub/
├── __init__.py          # Package initialization
├── cli.py               # Minimal Click-based CLI (TUI launcher, tracking commands)
├── tui.py               # Textual-based TUI interface (primary interface)
├── humble_wrapper.py    # Wrapper around humble-cli subprocess calls
├── epub_manager.py      # High-level bundle/item management logic
├── tracker.py           # SQLite-based download tracking
└── display.py           # Rich console formatting utilities
```

### Design Principles

1. **Focused Scope**: Avoid duplicating humble-cli; add complementary features only
2. **Separation of Concerns**: Each module handles a specific aspect of functionality
3. **Wrapper Pattern**: `humble_wrapper.py` abstracts humble-cli interactions
4. **Persistence Layer**: SQLite database tracks download history
5. **Rich UI**: Uses Rich and Textual for beautiful console output
6. **Error Handling**: Custom exceptions for humble-cli errors

---

## Module Descriptions

### 1. `humble_wrapper.py` - External Tool Wrapper

**Purpose**: Provides a Python interface to the `humble-cli` tool by wrapping subprocess calls.

**Key Functions**:

- `check_humble_cli()` - Verifies humble-cli is installed and available
- `get_bundles()` - Lists all purchased bundles (returns list of dicts with 'key' and 'name')
- `get_bundle_details(bundle_key)` - Gets raw details for a specific bundle
- `parse_bundle_details(details_output)` - Parses humble-cli output into structured data
- `search_bundles(keywords, mode)` - Searches bundles by keywords
- `download_bundle(bundle_key, output_dir, formats, ...)` - Downloads files from a bundle
- `download_item_format(bundle_key, item_number, format_name, output_dir)` - Downloads specific item format

**Design Notes**:

- All subprocess calls use `capture_output=True` for clean output handling
- Returns structured dictionaries rather than raw text when possible
- Raises `HumbleCLIError` for failed operations
- Parsing logic handles the text-based output format from humble-cli
- **Keys-Only Bundles**: The parser correctly handles bundles that contain only game keys with no downloadable items (common for game bundles). Previously had a bug where it would return early if no items table was found, skipping keys parsing

**Bundle Details Structure**:

```python
{
    'name': str,          # Bundle name
    'purchased': str,     # Purchase date
    'amount': str,        # Amount spent
    'total_size': str,    # Total bundle size
    'items': [            # List of downloadable items
        {
            'number': int,         # Item number (for --item-numbers)
            'name': str,           # Item name
            'formats': [str],      # Available formats (EPUB, PDF, MOBI)
            'size': str            # Item size
        }
    ],
    'keys': [             # Game keys in the bundle
        {
            'number': int,
            'name': str,
            'redeemed': bool
        }
    ]
}
```

---

### 2. `tracker.py` - Download Tracking

**Purpose**: Maintains a persistent record of downloaded files to avoid re-downloading.

**Database Schema**:

```sql
CREATE TABLE downloads (
    file_url TEXT PRIMARY KEY,      -- Unique identifier for the file
    bundle_key TEXT NOT NULL,        -- Bundle this file belongs to
    filename TEXT NOT NULL,          -- File name
    file_size TEXT,                  -- Human-readable size
    downloaded_at TIMESTAMP NOT NULL,-- When it was downloaded
    file_path TEXT                   -- Local path where saved
);

CREATE INDEX idx_bundle_key ON downloads(bundle_key);
```

**Key Methods**:

- `__init__(db_path)` - Initializes database at `~/.humblebundle/downloads.db`
- `mark_downloaded(file_url, bundle_key, filename, ...)` - Records a download
- `is_downloaded(file_url)` - Checks if file was already downloaded
- `get_bundle_stats(bundle_key, total_files)` - Returns download statistics for a bundle
- `get_all_stats()` - Returns overall statistics
- `get_downloaded_files(bundle_key)` - Lists downloaded files

**Design Notes**:

- Uses SQLite for zero-configuration persistence
- Supports upsert operations (INSERT OR REPLACE)
- File URL is used as primary key (unique identifier)
- Timestamps track when files were downloaded

---

### 3. `epub_manager.py` - Business Logic

**Purpose**: High-level API for finding and managing EPUB files, coordinating between humble-cli and the tracker.

**Key Methods**:

- `find_epub_bundles()` - Scans all bundles and returns those containing EPUBs
- `list_epubs_in_bundle(bundle_key)` - Lists EPUB files in a specific bundle
- `get_bundle_stats(bundle_key)` - Gets download statistics
- `get_bundle_items(bundle_key)` - Gets parsed bundle data with download status
- `download_item(bundle_key, item_number, format_name, output_dir)` - Downloads and tracks

**Design Notes**:

- Acts as a facade/orchestrator between components
- Handles the complexity of matching files to download status
- Creates unique identifiers for tracking: `{bundle_key}_{item_number}_{format}`
- Automatically marks downloads in the tracker

**Bundle Finding Strategy**:

1. Get all bundles from humble-cli
2. For each bundle, get details
3. Check if details contain "epub" or ".epub"
4. Count EPUB occurrences
5. Return bundles with EPUB count > 0

---

### 4. `display.py` - UI Formatting

**Purpose**: Provides Rich-formatted output for the CLI, abstracting console formatting.

**Key Functions**:

- `display_bundles(bundles, with_stats)` - Renders bundle table
- `display_epub_list(epubs, mark_downloaded)` - Renders EPUB file table
- `display_bundle_status(bundle_name, stats)` - Shows download progress panel
- `display_overall_stats(stats)` - Shows overall statistics panel
- `print_success/error/warning/info(message)` - Colored status messages
- `create_progress_bar(description)` - Creates Rich progress bar

**Features**:

- Tables with aligned columns and colors
- Progress bars and panels
- Unicode symbols (✓, ✗, ⚠, ℹ, etc.)
- Consistent styling throughout

---

### 5. `cli.py` - Command-Line Interface

**Purpose**: Provides a minimal Click-based CLI focused on TUI launching and download tracking.

**Design Philosophy**: This tool intentionally avoids duplicating `humble-cli` functionality. For listing bundles, searching, and downloading, users should use `humble-cli` directly. This tool adds value through:

1. Interactive TUI with visual navigation
2. Download tracking to prevent re-downloads
3. Progress statistics across bundles

**Commands**:

1. **`tui`** - Launch interactive TUI (primary interface)
   - `--output, -o`: Output directory
   - Provides keyboard-driven browsing and downloading
2. **`status [bundle_key]`** - Show download progress statistics

   - Without bundle_key: Shows overall stats across all bundles
   - With bundle_key: Shows specific bundle download status
   - Uses tracking database to calculate completion percentages

3. **`mark-downloaded <file_url> <bundle_key> <filename>`** - Manually mark file as downloaded
   - Useful for tracking files downloaded via humble-cli or web interface
   - Updates SQLite tracking database

**Removed Commands** (use `humble-cli` instead):

- ~~`list`~~ → Use `humble list`
- ~~`search`~~ → Use `humble search <keyword>`
- ~~`download`~~ → Use `humble download <bundle-key>`
- ~~`download-all`~~ → Use shell loop with `humble download`
- ~~`details`~~ → Use `humble details <bundle-key>`

**Context Management**:

- Uses Click's context to share tracker and epub_manager between commands
- `_ensure_initialized(ctx)` - Lazy initialization of shared objects
- Validates humble-cli availability before operations

---

### 6. `tui.py` - Text User Interface

**Purpose**: Provides an interactive, keyboard-driven interface using Textual.

**Components**:

#### `BundleListScreen`

- Shows all bundles in a scrollable list
- Keybindings:
  - `Enter`: Select bundle
  - `q`: Quit
  - `↑↓`: Navigate

#### `BundleDetailsScreen`

- Shows items in selected bundle
- Displays formats available for each item
- Shows download status per format
- Keybindings:
  - `Enter`: Download selected item/format
  - `←→`: Cycle through formats
  - `Escape`: Go back to bundle list
  - `↑↓`: Navigate items
  - `q`: Quit

#### `ItemFormatRow`

- Custom list item for items with multiple formats
- Shows download indicators: `[✓] EPUB | [ ] PDF | [ ] MOBI`
- Highlights selected format in cyan
- `cycle_format()`: Rotates through available formats

#### `HumbleBundleTUI` (Main App)

- Manages screen transitions
- Handles messages between screens
- Applies CSS styling
- Coordinates async operations

**Features**:

- Async loading with `@work` decorator for non-blocking UI
- Screen visibility toggling for navigation
- Format selection without re-downloading
- Real-time download status updates
- Game keys display (with redemption status)

**Design Notes**:

- Uses Textual's reactive programming model
- Custom messages (`BundleSelected`, `GoBack`) for screen communication
- CSS styling for consistent look
- Handles edge cases (empty bundles, keys-only bundles)

---

## Data Flow

### Bundle Discovery Flow

```
CLI/TUI → EPUBManager.find_epub_bundles()
    → HumbleWrapper.get_bundles()
    → For each bundle:
        → HumbleWrapper.get_bundle_details()
        → Check for "epub" in output
        → Count EPUBs
    → Return filtered list
```

### Download Flow

```
CLI/TUI → EPUBManager.download_item()
    → HumbleWrapper.download_item_format()
        → subprocess: humble-cli download
    → On success:
        → Tracker.mark_downloaded()
            → SQLite INSERT
```

### Status Check Flow

```
CLI/TUI → EPUBManager.get_bundle_items()
    → HumbleWrapper.get_bundle_details()
    → HumbleWrapper.parse_bundle_details()
    → For each item/format:
        → Tracker.is_downloaded()
            → SQLite SELECT
    → Return enriched data
```

---

## Configuration & Storage

### Database Location

- Default: `~/.humblebundle/downloads.db`
- Created automatically on first run
- Schema initialized by `tracker.py`

### Download Location

- Default: `~/Downloads/HumbleBundle/`
- Configurable via `--output` flag
- Creates directory structure automatically

### Dependencies

- **humble-cli**: Required external dependency
- **click**: CLI framework
- **rich**: Console formatting
- **textual**: TUI framework
- **sqlite3**: Built-in (Python standard library)

---

## Extension Points

### Adding New File Formats

The architecture is designed to handle any file format, not just EPUB:

1. **CLI**: Already supports `--format` flag for any format
2. **Wrapper**: `download_item_format()` accepts any format string
3. **Tracker**: Format-agnostic (tracks by file URL)
4. **Manager**: Can be extended with format-specific methods

Example:

```python
# Download PDFs instead
epub_manager.download_item(
    bundle_key="xyz",
    item_number=1,
    format_name="pdf",  # Just change this
    output_dir="/path"
)
```

### Adding New Commands

Create new Click commands in `cli.py`:

```python
@main.command()
@click.pass_context
def my_command(ctx):
    _ensure_initialized(ctx)
    epub_manager = ctx.obj['epub_manager']
    # Your logic here
```

### Custom Tracking

Extend `DownloadTracker` with new methods:

```python
def get_downloads_by_date(self, start_date, end_date):
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM downloads WHERE downloaded_at BETWEEN ? AND ?",
            (start_date, end_date)
        )
        return cursor.fetchall()
```

---

## Error Handling

### HumbleCLIError

- Raised when humble-cli commands fail
- Caught at CLI/TUI level
- Displays user-friendly error messages

### Exception Flow

```python
try:
    result = humble_wrapper.get_bundles()
except HumbleCLIError as e:
    print_error(str(e))
    sys.exit(1)
```

### Graceful Degradation

- If a bundle fails to load, skip it and continue
- TUI shows loading states and error messages
- CLI provides helpful installation instructions

---

## Performance Considerations

### Lazy Loading

- Bundle list loads quickly (just keys + names)
- Details loaded only when needed
- TUI uses async workers to avoid blocking

### Caching Strategy

- TUI maintains in-memory cache for bundle details
- Database indexes on bundle_key for fast queries
- Subprocess output captured efficiently

### Async Operations

- TUI uses `@work` decorator for background tasks
- Non-blocking UI during downloads
- Progress updates don't freeze interface

---

## Testing Strategy

### Manual Testing

The project includes test scripts:

- `test_cli.py` - Tests CLI commands
- `test_keys_parsing.py` - Tests bundle detail parsing
- `test_keys_debug.py` - Debugs key extraction

### Test Coverage Areas

1. **Parsing**: Bundle detail parsing (items, keys, formats)
2. **CLI**: Command execution and output
3. **Database**: Tracker insert/query operations
4. **Downloads**: Dry-run mode for testing without downloads

---

## Future Enhancements

### Potential Features

1. **Batch Operations**: Select multiple items in TUI
2. **Filters**: Filter by format, size, or download status
3. **Search in TUI**: Add search capability to TUI
4. **Resume Downloads**: Track partial downloads
5. **Export**: Export download history to CSV/JSON
6. **Notifications**: Desktop notifications on download completion
7. **Parallel Downloads**: Download multiple files simultaneously
8. **Bundle Groups**: Organize bundles into categories
9. **Auto-sync**: Periodically check for new bundles

### Architecture Improvements

1. **Config File**: Support for `~/.humblebundle/config.yaml`
2. **Plugin System**: Allow custom format handlers
3. **API Mode**: Expose functionality as REST API
4. **Web UI**: Browser-based interface
5. **Cloud Sync**: Sync download history across machines

---

## Deployment

### Installation

```bash
cd /path/to/project
pip install -e .
```

### Distribution

The project uses setuptools and can be packaged:

```bash
python -m build
pip install dist/humblebundle_epub-0.1.0-py3-none-any.whl
```

### Entry Point

The `hb-epub` command is registered in `pyproject.toml`:

```toml
[project.scripts]
hb-epub = "humblebundle_epub.cli:main"
```

---

## Dependencies Analysis

### Production Dependencies

- **click** (≥8.0.0): CLI framework, MIT license
- **rich** (≥13.0.0): Console formatting, MIT license
- **textual** (≥0.40.0): TUI framework, MIT license

### Development Dependencies

- **pytest** (≥7.0.0): Testing framework
- **black** (≥22.0.0): Code formatting

### External Tools

- **humble-cli**: Required, must be installed separately
  - Repository: https://github.com/tuxuser/humble-cli
  - Authentication required via session key

---

## Security Considerations

### Authentication

- Relies on humble-cli for authentication
- No credentials stored by this tool
- Session key stored by humble-cli

### File System

- Creates directories with default permissions
- Downloads to user-specified directory
- No elevation required

### Database

- SQLite file readable only by user (default OS permissions)
- No sensitive data stored (only download history)
- No user credentials in database

---

## Maintenance Notes

### Code Style

- Follows PEP 8
- Type hints for function signatures
- Docstrings for all public functions
- Black formatting

### Version Control

- Git repository at `/home/varigg/projects/python/humblebundle`
- Exploration scripts in `exploration/` (excluded from main code)

### Documentation

- README.md: User-facing documentation
- IMPLEMENTATION.md: This document (technical documentation)
- Inline comments for complex logic
- Docstrings follow Google style

---

## Summary

The Humble Bundle EPUB Manager is a well-architected CLI/TUI tool that:

1. **Wraps** humble-cli for Humble Bundle API access
2. **Tracks** downloads in SQLite database
3. **Manages** file discovery and downloading
4. **Displays** rich, formatted output
5. **Provides** both command-line and interactive interfaces

The modular design makes it easy to extend, maintain, and test. The use of established libraries (Click, Rich, Textual) ensures reliability and good UX.
