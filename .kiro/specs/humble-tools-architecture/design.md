# Humble Tools Architecture Design Document

## Overview

Humble Tools is a Python-based application suite that enhances the Humble Bundle experience by providing both interactive (TUI) and command-line (CLI) interfaces for library management. The system is built as a wrapper around the existing humble-cli tool, adding download tracking, progress monitoring, and enhanced user experience while maintaining compatibility with the proven humble-cli download engine.

The architecture follows a layered approach with clear separation of concerns:
- **Presentation Layer**: TUI (Textual) and CLI (Click) interfaces
- **Business Logic Layer**: Download management and coordination
- **Data Access Layer**: SQLite-based download tracking and humble-cli integration
- **External Integration**: Subprocess-based humble-cli wrapper

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
├─────────────────────────┬───────────────────────────────────┤
│     humble-sync         │         humble-track              │
│   (Textual TUI)         │        (Click CLI)                │
│                         │                                   │
│ • BundleListScreen      │ • status command                  │
│ • BundleDetailsScreen   │ • mark-downloaded command         │
│ • Interactive navigation│ • Scriptable operations           │
└─────────────────────────┴───────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                      │
├─────────────────────────────────────────────────────────────┤
│                  DownloadManager                            │
│                                                             │
│ • Bundle data coordination                                  │
│ • Download orchestration                                    │
│ • Status aggregation                                        │
│ • Format selection logic                                    │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                   Data Access Layer                         │
├─────────────────────────┬───────────────────────────────────┤
│    DownloadTracker      │        HumbleWrapper              │
│    (SQLite)             │      (subprocess)                 │
│                         │                                   │
│ • Download history      │ • humble-cli integration          │
│ • Progress tracking     │ • Command execution               │
│ • Statistics queries    │ • Output parsing                  │
│ • Manual marking        │ • Error handling                  │
└─────────────────────────┴───────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                  External Dependencies                      │
├─────────────────────────────────────────────────────────────┤
│                     humble-cli                              │
│                                                             │
│ • Authentication management                                 │
│ • Humble Bundle API interaction                             │
│ • File download operations                                  │
│ • Bundle and item discovery                                 │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Input → Presentation Layer → DownloadManager → Data Access Layer → humble-cli
     ↑                                    ↓
     └── Display/Rich ←── Business Logic ←┘
```

## Components and Interfaces

### Core Components

#### 1. DownloadManager
**Purpose**: Central coordinator for all download-related operations
**Responsibilities**:
- Aggregate bundle data with download status
- Orchestrate download operations
- Coordinate between tracking and external tool integration
- Provide unified interface for both TUI and CLI

**Key Methods**:
```python
def get_bundle_items(bundle_key: str) -> Dict
def download_item(bundle_key: str, item_number: int, format_name: str, output_dir: Path) -> bool
def get_bundle_stats(bundle_key: str) -> Dict
```

#### 2. DownloadTracker
**Purpose**: Persistent storage and querying of download history
**Responsibilities**:
- SQLite database management
- Download status tracking
- Progress statistics calculation
- Manual download marking

**Key Methods**:
```python
def mark_downloaded(file_url: str, bundle_key: str, filename: str, ...)
def is_downloaded(file_url: str) -> bool
def get_bundle_stats(bundle_key: str) -> Dict[str, Optional[int]]
def get_tracked_bundles() -> List[str]
```

#### 3. HumbleWrapper
**Purpose**: Interface to external humble-cli tool
**Responsibilities**:
- Subprocess command execution
- Output parsing and error handling
- Bundle and item data extraction
- Download delegation

**Key Methods**:
```python
def get_bundles() -> List[Dict[str, str]]
def get_bundle_details(bundle_key: str) -> str
def parse_bundle_details(details_output: str) -> Dict
def download_item_format(bundle_key: str, item_number: int, format_name: str, output_dir: str) -> bool
```

#### 4. Display Module
**Purpose**: Consistent formatting and output styling
**Responsibilities**:
- Rich console output formatting
- Table generation and styling
- Progress indicators and status messages
- Cross-component display consistency

### Interface Contracts

#### Bundle Data Structure
```python
{
    "name": str,
    "purchased": str,
    "amount": str, 
    "total_size": str,
    "items": [
        {
            "number": int,
            "name": str,
            "formats": List[str],
            "size": str,
            "format_status": Dict[str, bool]  # format -> downloaded
        }
    ],
    "keys": [
        {
            "number": int,
            "name": str,
            "redeemed": bool
        }
    ]
}
```

#### Statistics Structure
```python
{
    "downloaded": int,
    "remaining": Optional[int],
    "total": Optional[int]
}
```

## Data Models

### Database Schema

#### Downloads Table
```sql
CREATE TABLE downloads (
    file_url TEXT PRIMARY KEY,           -- Unique identifier for file
    bundle_key TEXT NOT NULL,            -- Bundle identifier
    filename TEXT NOT NULL,              -- Original filename
    file_size TEXT,                      -- Human-readable size
    downloaded_at TIMESTAMP NOT NULL,    -- Download timestamp
    file_path TEXT,                      -- Local file path
    bundle_total_files INTEGER           -- Total files in bundle
);

CREATE INDEX idx_bundle_key ON downloads(bundle_key);
```

### File Identification Strategy

Files are uniquely identified using a composite key:
```python
file_id = f"{bundle_key}_{item_number}_{format_name.lower()}"
```

This ensures that different formats of the same item are tracked separately, enabling format-specific download status.

### Configuration Data

#### Application Defaults
- Database location: `~/.humblebundle/downloads.db`
- Default download directory: `~/Downloads/HumbleBundle/`
- humble-cli dependency: External tool requirement

## Error Handling

### Error Categories and Strategies

#### 1. External Tool Errors
**Scenario**: humble-cli not installed, authentication failures, network issues
**Strategy**: 
- Graceful detection and user guidance
- Clear error messages with actionable steps
- Fallback to cached data where possible

#### 2. Database Errors
**Scenario**: SQLite file corruption, permission issues, disk space
**Strategy**:
- Automatic database initialization
- Graceful degradation (continue without tracking)
- Clear error reporting with recovery suggestions

#### 3. Parsing Errors
**Scenario**: humble-cli output format changes, malformed data
**Strategy**:
- Robust parsing with fallback handling
- Detailed error logging for debugging
- Partial data recovery where possible

#### 4. User Input Errors
**Scenario**: Invalid bundle keys, missing files, incorrect parameters
**Strategy**:
- Input validation and sanitization
- Helpful error messages with examples
- Suggestion of valid alternatives

### Error Handling Patterns

```python
class HumbleCLIError(Exception):
    """Specific exception for humble-cli related errors"""
    pass

def handle_humble_cli_errors(func):
    """Decorator for consistent error handling"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HumbleCLIError as e:
            print_error(str(e))
            sys.exit(1)
    return wrapper
```

## Testing Strategy

### Dual Testing Approach

The system employs both unit testing and property-based testing to ensure comprehensive coverage:

#### Unit Testing
- **Scope**: Specific examples, integration points, error conditions
- **Framework**: pytest with asyncio support
- **Coverage**: Component interfaces, error handling, edge cases
- **Focus**: Concrete behavior verification and regression prevention

#### Property-Based Testing  
- **Framework**: Hypothesis (Python property-based testing library)
- **Configuration**: Minimum 100 iterations per property test
- **Scope**: Universal properties that should hold across all inputs
- **Tagging**: Each property test tagged with format: `**Feature: humble-tools-architecture, Property {number}: {property_text}**`

The combination provides:
- Unit tests catch specific bugs and verify concrete examples
- Property tests verify general correctness across input space
- Together they ensure both specific functionality and universal behavior

### Test Organization
```
tests/
├── test_core/              # Core functionality tests
│   ├── test_download_manager.py
│   ├── test_humble_wrapper.py
│   ├── test_tracker.py
│   └── test_display.py
├── test_sync/              # TUI tests
│   └── test_app.py
└── test_track/             # CLI tests
    └── test_commands.py
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Bundle Selection Data Completeness
*For any* selected bundle, the displayed information should include items, formats, and download status for all available content
**Validates: Requirements 1.2**

### Property 2: UI Navigation State Consistency  
*For any* item navigation action, keyboard controls should correctly update the UI state and selected format
**Validates: Requirements 1.3**

### Property 3: Download Status Display Accuracy
*For any* item with download history, the visual indicators should accurately reflect the tracked download status
**Validates: Requirements 1.4**

### Property 4: Download Feedback Responsiveness
*For any* download operation, the UI should provide real-time feedback and update status indicators appropriately
**Validates: Requirements 1.5**

### Property 5: Download Persistence Guarantee
*For any* file downloaded through Humble_Tools, the Download_Tracker should successfully record the download in persistent storage
**Validates: Requirements 2.1**

### Property 6: Download Status Query Accuracy
*For any* file recorded as downloaded, querying the Download_Tracker should return accurate status information
**Validates: Requirements 2.2**

### Property 7: Visual Status Consistency
*For any* bundle content display, items marked as downloaded in the tracker should be visually indicated as such
**Validates: Requirements 2.3**

### Property 8: Statistical Accuracy
*For any* bundle statistics query, the counts of downloaded and remaining files should be mathematically consistent with the total
**Validates: Requirements 2.4**

### Property 9: Persistence Round-Trip
*For any* download information stored, restarting the application should preserve all historical data
**Validates: Requirements 2.5**

### Property 10: Bundle-Specific Status Display
*For any* valid bundle key provided to the status command, the system should show detailed progress for that specific bundle
**Validates: Requirements 3.2**

### Property 11: Statistics Display Completeness
*For any* statistics display, the output should include downloaded counts, remaining counts, and completion percentages
**Validates: Requirements 3.3**

### Property 12: Subprocess Command Delegation
*For any* bundle information request, the system should invoke appropriate humble-cli commands through subprocess calls
**Validates: Requirements 4.1**

### Property 13: Error Handling and Reporting
*For any* humble-cli command failure, the system should capture error output and present meaningful error messages
**Validates: Requirements 4.3**

### Property 14: Download Operation Delegation
*For any* download request, the system should delegate the actual download operation to humble-cli
**Validates: Requirements 4.4**

### Property 15: Output Parsing Robustness
*For any* humble-cli output, the parsing should handle various formats and edge cases without failure
**Validates: Requirements 4.5**

### Property 16: Format Display Completeness
*For any* bundle item with multiple formats, all available formats should be displayed to the user
**Validates: Requirements 6.1**

### Property 17: Format Navigation Functionality
*For any* item in the TUI, keyboard controls should allow cycling through all available formats
**Validates: Requirements 6.2**

### Property 18: Selected Format Visual Indication
*For any* format selection, the UI should visually highlight the currently selected format
**Validates: Requirements 6.3**

### Property 19: Format-Specific Download Targeting
*For any* download operation, only the currently selected format should be downloaded
**Validates: Requirements 6.4**

### Property 20: Format-Granular Tracking
*For any* download tracking, the Download_Tracker should record downloads per format to enable format-specific status
**Validates: Requirements 6.5**

### Property 21: Game Key Display Completeness
*For any* bundle containing game keys, the system should display key names and redemption status
**Validates: Requirements 7.1**

### Property 22: Redeemed Key Visual Indication
*For any* redeemed game key, the display should include appropriate visual markers
**Validates: Requirements 7.2**

### Property 23: Unredeemed Key Visual Distinction
*For any* unredeemed game key, the display should use distinct visual styling to highlight availability
**Validates: Requirements 7.3**

### Property 24: Key Information Parsing Accuracy
*For any* bundle details containing keys, the parsing should correctly extract key information from humble-cli output
**Validates: Requirements 7.5**

### Property 25: Manual Entry Recording
*For any* manual download marking, the Download_Tracker should record the entry with all provided metadata
**Validates: Requirements 8.1**

### Property 26: Manual Entry Query Inclusion
*For any* download status check, manually marked files should be included in status calculations
**Validates: Requirements 8.2**

### Property 27: Manual Entry Visual Consistency
*For any* manually marked file, the display should show it as downloaded with appropriate visual indicators
**Validates: Requirements 8.3**