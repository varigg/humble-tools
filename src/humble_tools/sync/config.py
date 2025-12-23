"""Configuration for the Humble Bundle TUI application."""

from dataclasses import dataclass
from pathlib import Path

from humble_tools.sync.constants import (
    DEFAULT_MAX_CONCURRENT_DOWNLOADS,
    DEFAULT_OUTPUT_DIR,
    ITEM_REMOVAL_DELAY_SECONDS,
    NOTIFICATION_DURATION_SECONDS,
)


@dataclass
class AppConfig:
    """Configuration for the Humble Bundle TUI application.

    Attributes:
        max_concurrent_downloads: Maximum number of simultaneous downloads
        notification_duration: How long notifications are displayed (seconds)
        item_removal_delay: Delay before removing completed items (seconds)
        output_dir: Directory where downloaded files are saved
    """

    max_concurrent_downloads: int = DEFAULT_MAX_CONCURRENT_DOWNLOADS
    notification_duration: int = NOTIFICATION_DURATION_SECONDS
    item_removal_delay: int = ITEM_REMOVAL_DELAY_SECONDS
    output_dir: Path = DEFAULT_OUTPUT_DIR

    def __post_init__(self):
        """Validate configuration values."""
        if self.max_concurrent_downloads < 1:
            raise ValueError("max_concurrent_downloads must be at least 1")
        if self.notification_duration < 1:
            raise ValueError("notification_duration must be at least 1")
        if self.item_removal_delay < 0:
            raise ValueError("item_removal_delay cannot be negative")

        # Ensure output_dir is a Path object
        if not isinstance(self.output_dir, Path):
            self.output_dir = Path(self.output_dir)
