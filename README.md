# Humble Tools

Two complementary tools for managing your Humble Bundle library, built on top of `humble-cli`:

- **humble-sync**: Interactive TUI for browsing and downloading
- **humble-track**: CLI for tracking download progress and statistics

## Why Use These Tools?

While `humble-cli` handles authentication and downloads, these tools add:

### 🎨 **Interactive TUI (humble-sync)**

- **Keyboard Navigation**: Browse bundles and items without typing commands
- **Visual Indicators**: Color-coded status, progress bars, and download markers (✓)
- **Format Cycling**: Press ←→ to switch between EPUB, PDF, MOBI before downloading
- **Context Preservation**: Navigate between views without losing your place

### 💾 **Download Tracking (humble-track)**

- **Automatic Prevention**: SQLite database prevents re-downloading files
- **Progress Statistics**: See downloaded vs remaining counts per bundle
- **Visual Status**: Items marked with ✓ when already downloaded
- **Resume Capability**: Track progress across multiple sessions

### 📊 **Enhanced Display**

- **Formatted Tables**: Rich console output for items and game keys
- **Bundle Statistics**: At-a-glance view of what's left to download
- **Keys Display**: Game key names shown with redemption status (✓ redeemed, yellow for not redeemed) - actual keys must be redeemed on Humble Bundle website
- **Organized Views**: Clean categorization of downloadable items vs game key listings

## Features

- 🖥️ **Interactive TUI**: Full-screen terminal UI for browsing and downloading
- 📊 **Progress tracking**: Visual statistics for downloaded vs remaining files
- ✅ **Download history**: SQLite database prevents re-downloading
- 🎮 **Keys management**: View game key names and redemption status (actual keys must be redeemed on Humble Bundle website)
- 🎯 **Format cycling**: Switch between EPUB, PDF, MOBI before downloading
- 🔄 **Status monitoring**: Track progress across all bundles
- 📝 **Manual tracking**: Mark externally downloaded files

## Prerequisites

- Python 3.8 or higher
- [humble-cli](https://github.com/smbl64/humble-cli) installed and authenticated

### Installing humble-cli

This project requires [humble-cli](https://github.com/smbl64/humble-cli) by [@smbl64](https://github.com/smbl64) - an excellent Rust-based command-line tool for interacting with your Humble Bundle library.

**Option 1: Download pre-built binaries (Recommended)**

Download the latest release for your platform from the [Releases page](https://github.com/smbl64/humble-cli/releases). Windows, macOS, and Linux are supported.

**Option 2: Install via Cargo**

If you have Rust installed:

```bash
cargo install humble-cli
```

**Verify installation:**

```bash
humble-cli --version
```

For more details, see the [humble-cli documentation](https://github.com/smbl64/humble-cli).

## Installation

```bash
# Install with uv
uv tool install .

# Or with pip
pip install .
```

## Authentication

First, authenticate with Humble Bundle using `humble-cli`:

```bash
humble-cli auth "YOUR_SESSION_KEY"
```

You can find your session key by logging into Humble Bundle in your browser and inspecting the `_simpleauth_sess` cookie.

## Usage

### humble-sync: Interactive TUI

Launch the interactive terminal UI for browsing and downloading:

```bash
humble-sync

# Or specify custom output directory
humble-sync --output /path/to/downloads
```

**Navigation:**

- `↑↓` - Navigate through bundles or items
- `Enter` - Select a bundle or download an item
- `←→` - Cycle through available formats (EPUB, PDF, MOBI, etc.)
- `Esc` - Go back to bundle list
- `q` - Quit the application

**Features:**

- See all bundles in a scrollable list
- View items and their available formats
- Visual indicators for already-downloaded files (✓)
- Real-time download status updates
- Game keys display with redemption status

### humble-track: CLI Commands

Track download progress and manage your library:

```bash
# Check download status for all bundles
humble-track status

# Check specific bundle
humble-track status <bundle-key>

# Manually mark a file as downloaded
humble-track mark-downloaded <file-url> <bundle-key> <filename>
```

### Use humble-cli for Core Operations

For listing, searching, and downloading files, use `humble-cli` directly:

```bash
# List all bundles
humble-cli list

# View bundle details
humble-cli details <bundle-key>

# Download from a bundle
humble-cli download <bundle-key>

# Search bundles
humble-cli search <keyword>
```

### Download Tracking

The tool maintains a SQLite database at `~/.humblebundle/downloads.db` to track which files have been downloaded. This provides several benefits:

- **Prevents duplicate downloads**: Already-downloaded files are marked with ✓
- **Resume capability**: Pick up where you left off across multiple sessions
- **Progress tracking**: See statistics showing downloaded vs remaining files
- **Per-bundle stats**: Know exactly which bundles still have content to download

The database only tracks download history - no credentials or sensitive data are stored.

## Configuration

### Download Location

Downloads are saved to `~/Downloads/HumbleBundle/` by default. You can specify a different directory:

```bash
humble-sync --output /path/to/directory
```

### Database Location

Download history is stored at `~/.humblebundle/downloads.db` by default. The database is created automatically on first run.

### Authentication

Authentication is handled by `humble-cli`. You must authenticate once before using this tool:

```bash
humble-cli auth "YOUR_SESSION_KEY"
```

Find your session key by:

1. Log into Humble Bundle in your browser
2. Open browser developer tools (F12)
3. Go to Application/Storage → Cookies
4. Find the `_simpleauth_sess` cookie value

## Use Cases

### Scenario 1: First-Time Library Review

```bash
# Launch TUI to browse your entire library
humble-sync

# Navigate through bundles, see what you have
# Download items selectively by pressing Enter
```

### Scenario 2: Track Download Progress

```bash
# See which bundles have undownloaded content
humble-track status

# Check a specific bundle
humble-track status <bundle-key>
```

### Scenario 3: Find and Download Specific Content

```bash
# Use humble-cli to search and list
humble-cli search "machine learning"
humble-cli list

# Use TUI to browse and download
humble-sync

# Or download with humble-cli
humble-cli download <bundle-key>

# Track progress
humble-track status <bundle-key>
```

### Scenario 4: Interactive Browsing

```bash
# Launch TUI for visual navigation
humble-sync

# Use keyboard to browse bundles
# Press Enter to download items
# See real-time download status
```

### Scenario 5: Review Game Keys

```bash
# Launch TUI and navigate to game bundles
humble-sync

# Key names are displayed with redemption status
# Green ✓ = redeemed, Yellow = not redeemed
# Actual key codes must be redeemed at https://www.humblebundle.com/home/keys
```

## Extending to Other Formats

While originally designed for EPUBs, these tools work with any file format available in your bundles. Use the `←→` arrow keys in the TUI to cycle through available formats (EPUB, PDF, MOBI, etc.) before downloading.

For command-line downloads with specific formats, use `humble-cli`:

```bash
# Download PDFs
humble-cli download <bundle-key> --format pdf

# Download multiple formats
humble-cli download <bundle-key> --format epub --format pdf
```

Supported formats include: `epub`, `pdf`, `mobi`, `azw3`, `cbz`, `mp3`, and more depending on your bundles.

## Troubleshooting

### "humble-cli is not installed"

Install humble-cli first: https://github.com/smbl64/humble-cli

Download the [latest release](https://github.com/smbl64/humble-cli/releases) or install via cargo:

```bash
cargo install humble-cli
```

### "Authentication failed"

Re-authenticate with humble-cli:

```bash
humble-cli auth "YOUR_SESSION_KEY"
```

### "Bundle not found"

Use humble-cli to find the exact bundle key:

```bash
# List all bundles
humble list

# Get bundle details
humble details <bundle-key>
```

### Downloads appear empty in TUI

Some bundles contain only game keys (no downloadable files). These are displayed with a keys table instead of download options.

### Already downloaded files showing as not downloaded

The tracking database only knows about files downloaded through these tools. Files downloaded directly via humble-cli or the website won't be tracked. You can manually mark files as downloaded:

```bash
humble-track mark-downloaded <file-url> <bundle-key> <filename>
```

## Architecture Overview

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ├─── humble-sync (TUI) ──────┐
       │                            │
       └─── humble-track (CLI) ─────┤
                                    │
                         ┌──────────▼──────────┐
                         │  Download Manager   │
                         │  (Business Logic)   │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
         ┌──────────▼─────────┐    │    ┌─────────▼────────┐
         │  Humble Wrapper    │    │    │  Download Tracker│
         │ (subprocess calls) │    │    │   (SQLite DB)    │
         └──────────┬─────────┘    │    └──────────────────┘
                    │               │
         ┌──────────▼─────────┐    │    ┌──────────────────┐
         │    humble-cli      │    │    │  Display/Rich    │
         │  (external tool)   │    │    │  (formatting)    │
         └────────────────────┘    └────┴──────────────────┘
```

### Project Structure

```
humble-tools/
├── src/humble_tools/
│   ├── core/              # Shared functionality
│   │   ├── humble_wrapper.py   # humble-cli interface
│   │   ├── tracker.py          # SQLite download tracking
│   │   ├── display.py          # Rich console formatting
│   │   └── download_manager.py # Download logic
│   ├── sync/              # TUI application (humble-sync)
│   │   └── app.py              # Textual-based interface
│   └── track/             # CLI commands (humble-track)
│       └── commands.py         # Click-based commands
└── tests/
    ├── test_core/         # Core functionality tests
    ├── test_sync/         # TUI tests
    └── test_track/        # CLI tests (to be added)
```

The tools act as a friendly wrapper around humble-cli, adding tracking, filtering, and enhanced UI while leveraging humble-cli's proven download capabilities.

## Contributing

The project uses `uv` for dependency management and development:

```bash
# Clone the repository
git clone https://github.com/varigg/humble-tools
cd humble-tools

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/humble_tools

# Install in development mode
uv pip install -e .
```

## License

See LICENSE file for details.

## Credits

- Built on top of [humble-cli](https://github.com/smbl64/humble-cli) by [@smbl64](https://github.com/smbl64)
- Uses [Click](https://click.palletsprojects.com/) for CLI
- Uses [Textual](https://textual.textualize.io/) for TUI
- Uses [Rich](https://rich.readthedocs.io/) for formatting

## Development

The project uses `uv` for dependency management:

```bash
# Clone the repository
git clone https://github.com/varigg/humble-tools
cd humble-tools

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Format code
uv run ruff format .

# Install in development mode
uv pip install -e .
```

## License

MIT
