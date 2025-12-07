"""High-level download management logic."""

from pathlib import Path
from typing import Dict, Optional

from humble_tools.core.humble_wrapper import (
    download_item_format,
    get_bundle_details,
    parse_bundle_details,
)
from humble_tools.core.tracker import DownloadTracker


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


class DownloadManager:
    """Manage file discovery and downloads."""

    def __init__(self, tracker: Optional[DownloadTracker] = None):
        """Initialize download manager.

        Args:
            tracker: Download tracker instance. Creates new one if None.
        """
        self.tracker = tracker or DownloadTracker()

    def get_bundle_stats(self, bundle_key: str) -> Dict:
        """Get download statistics for a bundle.

        Args:
            bundle_key: Bundle identifier

        Returns:
            Statistics dictionary
        """
        return self.tracker.get_bundle_stats(bundle_key)

    def get_bundle_items(self, bundle_key: str) -> Dict:
        """Get parsed bundle data with download status for each item format.

        Args:
            bundle_key: Bundle identifier

        Returns:
            Dictionary with bundle metadata and items list with download status
        """
        details_output = get_bundle_details(bundle_key)
        bundle_data = parse_bundle_details(details_output)

        # Add download status for each item format
        for item in bundle_data["items"]:
            item["format_status"] = {}
            for fmt in item["formats"]:
                # Create unique identifier for this specific format
                file_id = _create_file_id(bundle_key, item["number"], fmt)
                item["format_status"][fmt] = self.tracker.is_downloaded(file_id)

        return bundle_data

    def download_item(
        self, bundle_key: str, item_number: int, format_name: str, output_dir: Path
    ) -> bool:
        """Download a specific format of an item and track it.

        Args:
            bundle_key: Bundle identifier
            item_number: Item number from bundle
            format_name: Format to download (e.g., 'epub')
            output_dir: Directory to save download

        Returns:
            True if successful
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get bundle items to determine total count for this format
        try:
            bundle_data = self.get_bundle_items(bundle_key)
            # Count items that have this format
            bundle_total = sum(
                1
                for item in bundle_data["items"]
                if format_name.upper() in item["formats"]
            )
        except Exception:
            # If we can't get bundle data, set total to None
            bundle_total = None

        # Download the file
        success = download_item_format(
            bundle_key=bundle_key,
            item_number=item_number,
            format_name=format_name,
            output_dir=str(output_dir),
        )

        if success:
            # Mark as downloaded
            file_id = _create_file_id(bundle_key, item_number, format_name)
            filename = f"item_{item_number}.{format_name.lower()}"
            self.tracker.mark_downloaded(
                file_url=file_id,
                bundle_key=bundle_key,
                filename=filename,
                bundle_total_files=bundle_total,
            )

        return success
