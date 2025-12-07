"""Wrapper functions for humble-cli commands."""

import re
import subprocess
from typing import Dict, List


class HumbleCLIError(Exception):
    """Exception raised when humble-cli command fails."""
    pass




def check_humble_cli() -> bool:
    """Check if humble-cli is installed and available.
    
    Returns:
        True if humble-cli is available, False otherwise
    """
    try:
        subprocess.run(
            ["humble-cli", "--version"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_bundles() -> List[Dict[str, str]]:
    """Get list of all purchased bundles.
    
    Returns:
        List of dictionaries with 'key' and 'name' fields
        
    Raises:
        HumbleCLIError: If humble-cli command fails
    """
    try:
        print("Listing bundles...")
        result = subprocess.run(
            ["humble-cli", "list", "--field", "key", "--field", "name"],
            capture_output=True,
            text=True,
            check=True
        )
        
        bundles = []
        lines = result.stdout.strip().split('\n')
        
        # Parse output: each bundle is "key,name"
        for line in lines:
            if ',' in line:
                parts = line.split(',', 1)  # Split on first comma only
                if len(parts) == 2:
                    bundles.append({
                        'key': parts[0].strip(),
                        'name': parts[1].strip()
                    })
        
        return bundles
    except subprocess.CalledProcessError as e:
        raise HumbleCLIError(f"Failed to list bundles: {e.stderr}")


def get_bundle_details(bundle_key: str) -> str:
    """Get detailed information about a bundle.
    
    Args:
        bundle_key: Bundle identifier (can be partial)
        
    Returns:
        Raw output from humble-cli details command
        
    Raises:
        HumbleCLIError: If humble-cli command fails
    """
    try:
        result = subprocess.run(
            ["humble-cli", "details", bundle_key],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise HumbleCLIError(f"Failed to get bundle details: {e.stderr}")


def _parse_bundle_name(lines: list) -> str:
    """Extract bundle name from the first non-empty line.
    
    Args:
        lines: List of output lines
        
    Returns:
        Bundle name or empty string if not found
    """
    if lines and lines[0].strip():
        return lines[0].strip()
    return ''


def _parse_metadata_field(lines: list, field_name: str) -> str:
    """Extract a metadata field value from bundle details.
    
    Args:
        lines: List of output lines
        field_name: Field to search for (e.g., 'Purchased', 'Amount spent')
        
    Returns:
        Field value or empty string if not found
    """
    for line in lines:
        if field_name in line:
            match = re.search(rf'{field_name}\s*:\s*(.+)', line)
            if match:
                return match.group(1).strip()
    return ''


def _parse_items_table(lines: list) -> list:
    """Parse the items table from bundle details.
    
    Args:
        lines: List of output lines
        
    Returns:
        List of items, each containing number, name, formats, and size
    """
    items = []
    
    # Find the table header line
    table_start = -1
    for i, line in enumerate(lines):
        if re.match(r'\s*#\s*\|\s*Sub-item', line):
            table_start = i + 2  # Skip header and separator line
            break
    
    if table_start == -1:
        return items
    
    # Parse items table
    for line in lines[table_start:]:
        line = line.strip()
        if not line:
            continue
        
        # Stop if we hit a section header like "Keys in this bundle:"
        if line.endswith(':'):
            break
        
        # Parse table row: # | Sub-item | Format | Total Size
        # Example: "  1 | Falcon Guard (Legend of the Jade Phoenix, Book Three) | MOBI, EPUB |   3.47 MiB"
        match = re.match(r'\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(.+)', line)
        if match:
            item_number = int(match.group(1))
            item_name = match.group(2).strip()
            formats_str = match.group(3).strip()
            size = match.group(4).strip()
            
            # Parse formats (comma-separated)
            formats = [fmt.strip().upper() for fmt in formats_str.split(',')]
            
            items.append({
                'number': item_number,
                'name': item_name,
                'formats': formats,
                'size': size
            })
    
    return items


def _parse_keys_table(lines: list) -> list:
    """Parse the keys table from bundle details.
    
    Args:
        lines: List of output lines
        
    Returns:
        List of keys, each containing number, name, and redeemed status
    """
    keys = []
    
    # Find the "Keys in this bundle:" line
    keys_start = -1
    for i, line in enumerate(lines):
        if 'Keys in this bundle:' in line:
            keys_start = i + 1
            break
    
    if keys_start == -1:
        return keys
    
    # Find the table header
    keys_table_start = -1
    for i in range(keys_start, len(lines)):
        if re.match(r'\s*#\s*\|\s*Key Name', lines[i]):
            keys_table_start = i + 2  # Skip header and separator
            break
    
    if keys_table_start == -1:
        return keys
    
    # Parse keys table
    for line in lines[keys_table_start:]:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Stop if we hit "Visit https://" line
        if line_stripped.startswith('Visit'):
            break
        
        # Parse key row: # | Key Name | Redeemed
        # Example: "  1 | Train Simulator Classic                                 |   Yes    "
        match = re.match(r'\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(.+)', line)
        if match:
            key_number = int(match.group(1))
            key_name = match.group(2).strip()
            redeemed = match.group(3).strip()
            
            keys.append({
                'number': key_number,
                'name': key_name,
                'redeemed': redeemed == 'Yes'
            })
    
    return keys


def parse_bundle_details(details_output: str) -> Dict:
    """Parse bundle details output into structured data.
    
    Args:
        details_output: Raw output from humble-cli details command
        
    Returns:
        Dictionary containing:
            - name: Bundle name
            - purchased: Purchase date
            - amount: Amount spent
            - total_size: Total bundle size
            - items: List of items, each with:
                - number: Item number
                - name: Item name
                - formats: List of available formats (e.g., ['EPUB', 'MOBI'])
                - size: Total size for this item
            - keys: List of keys, each with:
                - number: Key number
                - name: Key name
                - redeemed: Boolean indicating if key is redeemed
                
    Raises:
        HumbleCLIError: If parsing fails
    """
    lines = details_output.strip().split('\n')
    
    return {
        'name': _parse_bundle_name(lines),
        'purchased': _parse_metadata_field(lines, 'Purchased'),
        'amount': _parse_metadata_field(lines, 'Amount spent'),
        'total_size': _parse_metadata_field(lines, 'Total size'),
        'items': _parse_items_table(lines),
        'keys': _parse_keys_table(lines)
    }


def download_item_format(
    bundle_key: str,
    item_number: int,
    format_name: str,
    output_dir: str
) -> bool:
    """Download a specific format from a specific item in a bundle.
    
    Args:
        bundle_key: Bundle identifier
        item_number: Item number from the bundle details table
        format_name: Format to download (e.g., 'epub', 'mobi')
        output_dir: Directory to save the download
        
    Returns:
        True if download succeeded
        
    Raises:
        HumbleCLIError: If download fails
    """
    cmd = [
        "humble-cli", "download", bundle_key,
        "--format", format_name.lower(),
        "--item-numbers", str(item_number)
    ]
    
    try:
        subprocess.run(
            cmd,
            cwd=output_dir,
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        raise HumbleCLIError(f"Failed to download item {item_number} ({format_name}): {e.stderr}")

