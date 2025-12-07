"""High-level download management logic."""

import re
from pathlib import Path
from typing import Dict, List, Optional

from humble_tools.core.humble_wrapper import (
    HumbleCLIError,
    download_item_format,
    get_bundle_details,
    get_bundles,
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


class EpubManager:
    """Manage file discovery and downloads."""
    
    def __init__(self, tracker: Optional[DownloadTracker] = None):
        """Initialize EPUB manager.
        
        Args:
            tracker: Download tracker instance. Creates new one if None.
        """
        self.tracker = tracker or DownloadTracker()
    
    def find_epub_bundles(self) -> List[Dict]:
        """Find all bundles containing EPUB files.
        
        Returns:
            List of bundle dictionaries with EPUB information
        """
        all_bundles = get_bundles()
        epub_bundles = []
        
        for bundle in all_bundles:
            try:
                details = get_bundle_details(bundle['key'])
                
                # Check if bundle contains EPUB files
                if 'epub' in details.lower() or '.epub' in details.lower():
                    epub_count = self._count_epubs_in_details(details)
                    if epub_count > 0:
                        bundle['epub_count'] = epub_count
                        epub_bundles.append(bundle)
            except HumbleCLIError:
                # Skip bundles that can't be accessed
                continue
        
        return epub_bundles
    
    def _count_epubs_in_details(self, details: str) -> int:
        """Count EPUB files mentioned in bundle details.
        
        Args:
            details: Raw output from humble-cli details
            
        Returns:
            Number of EPUB files found
        """
        # Count occurrences of .epub (case insensitive)
        return len(re.findall(r'\.epub\b', details, re.IGNORECASE))
    
    def list_epubs_in_bundle(self, bundle_key: str) -> List[Dict]:
        """List all EPUB files in a bundle with download status.
        
        Args:
            bundle_key: Bundle identifier
            
        Returns:
            List of EPUB file dictionaries with metadata
        """
        details = get_bundle_details(bundle_key)
        epubs = self._parse_epubs_from_details(details)
        
        # Mark which files are already downloaded
        for epub in epubs:
            # Use filename as a simple identifier
            # In a real scenario, we'd need the actual URL
            epub['downloaded'] = False  # TODO: Implement proper URL tracking
        
        return epubs
    
    def _parse_epubs_from_details(self, details: str) -> List[Dict]:
        """Parse EPUB file information from bundle details.
        
        Args:
            details: Raw output from humble-cli details
            
        Returns:
            List of EPUB file dictionaries
        """
        epubs = []
        lines = details.split('\n')
        
        current_item = None
        for line in lines:
            line = line.strip()
            
            # Look for item headers (usually numbered or bulleted)
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # This might be a new item
                current_item = {'name': line, 'formats': []}
            
            # Look for EPUB format mentions
            if 'epub' in line.lower():
                # Try to extract file size if present
                size_match = re.search(r'(\d+\.?\d*\s*[KMG]B)', line, re.IGNORECASE)
                size = size_match.group(1) if size_match else 'N/A'
                
                # Try to extract filename
                name_match = re.search(r'([^/\\]+\.epub)', line, re.IGNORECASE)
                name = name_match.group(1) if name_match else (current_item['name'] if current_item else 'Unknown')
                
                epubs.append({
                    'name': name,
                    'format': 'epub',
                    'size': size,
                    'downloaded': False
                })
        
        return epubs
    
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
        for item in bundle_data['items']:
            item['format_status'] = {}
            for fmt in item['formats']:
                # Create unique identifier for this specific format
                file_id = _create_file_id(bundle_key, item['number'], fmt)
                item['format_status'][fmt] = self.tracker.is_downloaded(file_id)
        
        return bundle_data
    
    def download_item(
        self,
        bundle_key: str,
        item_number: int,
        format_name: str,
        output_dir: Path
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
                1 for item in bundle_data['items'] 
                if format_name.upper() in item['formats']
            )
        except Exception:
            # If we can't get bundle data, set total to None
            bundle_total = None
        
        # Download the file
        success = download_item_format(
            bundle_key=bundle_key,
            item_number=item_number,
            format_name=format_name,
            output_dir=str(output_dir)
        )
        
        if success:
            # Mark as downloaded
            file_id = _create_file_id(bundle_key, item_number, format_name)
            filename = f"item_{item_number}.{format_name.lower()}"
            self.tracker.mark_downloaded(
                file_url=file_id,
                bundle_key=bundle_key,
                filename=filename,
                bundle_total_files=bundle_total
            )
        
        return success

