# Bundle Keys Parsing and Display Review

## Issue Identified

Bundles containing only game keys (no downloadable items) were not showing any details in the TUI.

## Root Cause

In `humble_wrapper.py`, the `parse_bundle_details()` function had an early return when no items table was found:

```python
if table_start == -1:
    return result  # No items table found - THIS WAS THE BUG
```

This prevented the function from continuing to the keys parsing section, so bundles with only keys would return an empty result.

## Fix Applied

Removed the early return and wrapped the items parsing in a conditional block:

```python
# Parse items table if found
if table_start != -1:
    # ... parse items ...

# Parse keys section continues regardless of whether items were found
```

Additionally added a safety check to stop items parsing if we encounter a section header (like "Keys in this bundle:"):

```python
# Stop if we hit a section header like "Keys in this bundle:"
if line.endswith(':'):
    break
```

## TUI Handling (Already Correct)

The TUI in `tui.py` already has proper handling for keys-only bundles:

```python
if not self.bundle_data['items']:
    # Check if there are keys to display
    if self.bundle_data.get('keys'):
        # Show keys table with proper formatting
        # Display header row
        # Display each key with redemption status
        # Set focus to first key
```

Features:

- Shows key count in status message
- Displays keys in a formatted table with columns: # | Key Name | Redeemed
- Color codes redemption status (green for redeemed, yellow for not redeemed)
- Provides helpful message to visit Humble Bundle website for redemption
- Properly handles focus and navigation

## Test Results

After the fix, the test bundle parses correctly:

```
Parsed bundle name: Train Simulator: All Aboard! Bundle
Number of items: 0
Number of keys: 6

Keys:
  1: Train Simulator Classic - Redeemed: True
  2: BR Class 170 'Turbostar' DMU Add-On - Redeemed: True
  3: Thompson Class B1 Loco Add-On - Redeemed: False
  4: DB BR 648 Loco Add-On - Redeemed: False
  5: Grand Central Class 180 'Adelante' DMU Add-On - Redeemed: False
  6: Peninsula Corridor: San Francisco - Gilroy Route Add-On - Redeemed: True
```

## Impact

- Keys-only bundles (like game bundles) now display correctly in both CLI and TUI
- Users can see their game keys and redemption status
- No regression for bundles with downloadable items
- Mixed bundles (items + keys) also work correctly

## Files Modified

- `src/humblebundle_epub/humble_wrapper.py` - Fixed `parse_bundle_details()` function
