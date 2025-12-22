# Specification: Concurrent Downloads in humble-sync

## Overview

Currently, the humble-sync TUI blocks user interaction while a file downloads. This specification describes the transition to asynchronous concurrent downloads, allowing users to queue multiple downloads and continue navigating the interface while downloads proceed in the background.

## Current State (Blocking Downloads)

- User selects an item with Enter
- TUI blocks and downloads the file synchronously
- User must wait for download to complete before navigating elsewhere
- No indication of progress during the download
- Single file downloads at a time

## Desired State (Concurrent Downloads)

- User selects an item with Enter
- Download starts immediately in background
- Item shows "⏳ Downloading..." status text
- User is immediately free to navigate and queue other downloads
- Multiple downloads proceed concurrently (configurable limit)
- Completed downloads are recorded to database (checkmark appears automatically)
- Active downloads are visible in the UI
- Finished downloads disappear from view after a brief delay
- Notifications appear when downloads complete or fail

## User Experience

### Download Initiation

When user presses Enter on an undownloaded item:

1. Item status immediately changes to "⏳ Downloading..."
2. Download task is queued/started in background
3. User regains control of the TUI immediately
4. User can navigate to other items and press Enter to queue more downloads
5. The checkmark already appears for downloaded items (existing UI behavior)

### Active Downloads Display

The TUI should clearly show:

- Which items are currently downloading (status text: "⏳ Downloading...")
- Download count: e.g., "Active Downloads: 2/3" indicating 2 of 3 concurrent limit
- Completed downloads automatically show checkmark (existing UI shows this for tracked files)

### Completion Feedback

When a download completes:

1. Item is recorded to tracker database
2. Item checkmark appears automatically (existing UI behavior)
3. Item's "⏳ Downloading..." status text is removed
4. A notification appears at the bottom of the screen (toast/banner style) with message like:
   - "✓ Downloaded: Game Title (EPUB format)"
   - or brief error message if failed
5. Item disappears from active downloads view after ~5-10 seconds
6. If user navigates back to the bundle, the item now shows with checkmark (already downloaded)

### Error Handling

If a download fails:

1. Item status changes to "❌ Error" or "⚠ Failed"
2. A notification appears with error details
3. User can retry by pressing Enter again on the failed item
4. Item remains visible for user action

### Navigation During Downloads

- User can scroll through bundle items while downloads are in progress
- User can navigate to different bundles
- User can cycle formats (←→) on any item
- Active downloads continue regardless of navigation

## Technical Requirements

### Asynchronous Architecture

- Downloads must run in background threads/tasks, not blocking the main TUI event loop
- Use asyncio and/or threading to manage concurrent downloads
- Textual's async support should be leveraged

### Concurrency Control

- **Default Limit**: 3 concurrent downloads (sensible default for most connections)
- **Configuration**: Users can set limit via:
  - Command-line flag: `humble-sync --max-downloads 5`
  - Configuration file: `~/.humblebundle/config.toml` or similar
- **Implementation**: Queue-based system with worker threads/tasks

### State Management

Each download tracks:

- `status`: "queued", "downloading", "completed", "failed"
- `progress`: Current bytes / total bytes (optional for future enhancement)
- `error_message`: Message if failed
- `start_time`: When download began
- `end_time`: When download finished
- `bundle_key`: Which bundle this item belongs to
- `item_number`: Item identifier within bundle
- `format_name`: File format (epub, pdf, mobi, etc.)

### Database Integration

- Downloads are recorded to SQLite tracker immediately upon completion
- Tracker prevents duplicate downloads (existing behavior preserved)
- Failed downloads are NOT recorded to tracker
- User can manually mark completed downloads if needed

### UI Updates

- Item rows update in real-time as download status changes
- Status column shows current status text:
  - "⏳ Downloading..." (active)
  - (empty/removed when complete - checkmark appears in existing column)
  - "❌ Error" or "⚠ Failed" (failed)
- Visual distinction (color) for each status state:
  - Blue/Cyan for downloading
  - Checkmark column shows ✓ for completed (existing UI)
  - Red for failed
  - Yellow/Orange for warnings

## Implementation Details

### Component Changes

#### DownloadManager (src/humble_tools/core/download_manager.py)

**Current**: Synchronous `download_item()` method blocks until complete

**New**:

- Modify to support async downloads
- Return immediately with download task/future
- Accept `on_progress` callback for status updates
- Track download state for each concurrent operation

#### BundleDetailsScreen (src/humble_tools/sync/app.py)

**Changes**:

- Add async action handler for Enter key on items
- Queue download instead of blocking
- Update item row UI as download progresses
- Listen for completion notifications
- Implement auto-removal of finished items after delay

#### TUI Application (src/humble_tools/sync/app.py)

**New**:

- Download queue/manager for coordinating concurrent downloads
- Download worker pool (default 3 workers)
- Message passing system for download status updates
- Configuration for max concurrent downloads
- Notification/toast system for completion messages

### Configuration Options

Add to humble-sync CLI or config file:

```bash
# Command line
humble-sync --max-downloads 5 --output /path/to/downloads

# Config file (~/.humblebundle/config.toml)
[downloads]
max_concurrent = 3
notification_delay = 10  # seconds before completed items disappear
```

### Notification System

Implement a simple toast/banner notification:

- Display at bottom of TUI
- Show for 3-5 seconds then fade
- Include download name and format
- Display success or error status
- Stack multiple notifications if needed

### Testing Strategy

#### Unit Tests

- Download queue behavior (adding, removing, limiting)
- State transitions (queued → downloading → completed)
- Error handling and retry logic
- Concurrent access to item status

#### Integration Tests

- TUI with mock humble-cli
- Multiple concurrent downloads
- User navigation while downloading
- Download completion and UI updates
- Notification display and removal

#### Manual Testing

- Download multiple items in sequence
- Download multiple items concurrently
- Cancel/retry failed downloads
- Navigation during downloads
- Verify database updates

## Backward Compatibility

- Existing tracker database format unchanged
- `download_item()` API changes but internal to application
- No CLI command changes needed
- User-visible behavior enhanced but not breaking

## Future Enhancements

These are out of scope for this specification but worth noting:

1. **Download Progress**: Show percentage/bytes downloaded per item
2. **Pause/Resume**: Allow pausing active downloads
3. **Speed Throttling**: Limit bandwidth usage
4. **Retry Strategy**: Automatic retry with exponential backoff
5. **Download Queue Persistence**: Save queue to disk for resume across sessions
6. **Bandwidth Monitoring**: Show current download speed
7. **Priority Queue**: User-defined download priority

## Success Criteria

- ✅ User can queue multiple downloads without blocking
- ✅ Active downloads are visible with "⏳ Downloading..." status
- ✅ Concurrent downloads respect configurable limit (default 3)
- ✅ Completed downloads show checkmark in existing UI column
- ✅ Completed downloads disappear from active view after ~5-10 seconds
- ✅ Notifications appear on completion/failure
- ✅ User can navigate and interact with TUI during downloads
- ✅ Download database updates correctly
- ✅ All existing tests pass
- ✅ New tests cover concurrent download behavior

## Risk Assessment

### Low Risk

- Notification system (isolated UI component)
- Configuration options (additive only)

### Medium Risk

- Download state management (new complexity)
- UI update timing (potential race conditions)

### Higher Risk

- Background task management (need careful thread/async safety)
- Database writes during concurrent downloads (potential conflicts)

### Mitigation

- Thorough unit tests for concurrent access
- Use thread-safe queues for communication
- Test with actual humble-cli to catch subprocess issues
- Add comprehensive logging for debugging

## Timeline Estimate

- Planning/Design: 2-4 hours
- Implementation: 8-12 hours
- Testing: 4-6 hours
- Documentation/Polish: 2-3 hours
- **Total**: ~20 hours of development work
