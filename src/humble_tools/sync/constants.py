"""Constants for the Humble Bundle TUI application."""

from pathlib import Path

# Download Configuration Defaults
DEFAULT_MAX_CONCURRENT_DOWNLOADS = 3
NOTIFICATION_DURATION_SECONDS = 5
ITEM_REMOVAL_DELAY_SECONDS = 10

# Display Configuration
MAX_ITEM_NAME_DISPLAY_LENGTH = 50
FORMAT_DISPLAY_WIDTH = 30
ITEM_NUMBER_WIDTH = 3
SIZE_DISPLAY_WIDTH = 10


# Widget IDs
class WidgetIds:
    """Widget selector IDs used throughout the application."""

    # Bundle List Screen
    BUNDLE_LIST = "bundle-list"
    STATUS_TEXT = "status-text"
    SCREEN_HEADER = "screen-header"

    # Bundle Details Screen
    BUNDLE_HEADER = "bundle-header"
    BUNDLE_METADATA = "bundle-metadata"
    ITEMS_LIST = "items-list"
    DETAILS_STATUS = "details-status"
    NOTIFICATION_AREA = "notification-area"


# Status Symbols
class StatusSymbols:
    """Unicode symbols for item status indicators."""

    DOWNLOADED = "✓"
    DOWNLOADING = "⏳"
    QUEUED = "🕒"
    NOT_DOWNLOADED = " "
    FAILED = "✗"


# Color Names (Textual Rich markup)
class Colors:
    """Color names for Textual Rich markup."""

    SUCCESS = "green"
    ERROR = "red"
    WARNING = "yellow"
    INFO = "blue"
    SELECTED = "bold cyan"
    MUTED = "text-muted"


# Default Paths
# Note: Database paths (DEFAULT_DATA_DIR, DEFAULT_DATABASE_PATH) are defined in
# humble_tools.core.database to avoid circular imports
DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "HumbleBundle"
