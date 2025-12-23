"""Textual-based TUI for Humble Bundle EPUB Manager."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

from humble_tools.core.download_manager import DownloadManager
from humble_tools.core.exceptions import APIError, DownloadError, HumbleToolsError
from humble_tools.core.humble_wrapper import HumbleCLIError, get_bundles
from humble_tools.core.tracker import DownloadTracker
from humble_tools.sync.config import AppConfig
from humble_tools.sync.constants import (
    FORMAT_DISPLAY_WIDTH,
    ITEM_NUMBER_WIDTH,
    MAX_ITEM_NAME_DISPLAY_LENGTH,
    SIZE_DISPLAY_WIDTH,
    Colors,
    StatusSymbols,
    WidgetIds,
)
from humble_tools.sync.download_queue import DownloadQueue


class BundleItem(ListItem):
    """A list item representing a bundle."""

    def __init__(self, bundle_key: str, bundle_name: str):
        super().__init__()
        self.bundle_key = bundle_key
        self.bundle_name = bundle_name

    def compose(self) -> ComposeResult:
        yield Label(self.bundle_name)


class ItemFormatRow(ListItem):
    """A list item representing an item with its formats."""

    # Reactive property that triggers display updates
    selected_format = reactive(None)

    def __init__(
        self,
        item_number: int,
        item_name: str,
        formats: List[str],
        item_size: str,
        format_status: Dict[str, bool],
        selected_format: Optional[str] = None,
    ):
        super().__init__()
        self.item_number = item_number
        self.item_name = item_name
        self.formats = formats
        self.item_size = item_size
        self.format_status = format_status
        self.format_downloading: Dict[
            str, bool
        ] = {}  # Track which formats are downloading
        self.format_queued: Dict[str, bool] = {}  # Track which formats are queued
        self._display_label: Optional[Label] = None
        # Set selected_format after super().__init__() to trigger reactive update
        self.selected_format = selected_format or (formats[0] if formats else None)

    def compose(self) -> ComposeResult:
        """Compose the row with a single label that will be updated reactively."""
        self._display_label = Label(self._build_display_text())
        yield self._display_label

    def _get_status_indicator(self, fmt: str) -> tuple[str, Optional[str]]:
        """Get status indicator and color for a format.

        Priority: queued > downloading > downloaded > not downloaded

        Args:
            fmt: Format name to check status for

        Returns:
            Tuple of (indicator_symbol, color_name)
            Colors: "blue" (queued), "yellow" (downloading), "green" (downloaded), None (available)
        """
        if self.format_queued.get(fmt, False):
            return StatusSymbols.QUEUED, Colors.INFO  # Queued
        elif self.format_downloading.get(fmt, False):
            return StatusSymbols.DOWNLOADING, Colors.WARNING  # Downloading
        elif self.format_status.get(fmt, False):
            return StatusSymbols.DOWNLOADED, Colors.SUCCESS  # Downloaded
        else:
            return StatusSymbols.NOT_DOWNLOADED, None  # Not downloaded

    def _format_single_item(
        self,
        fmt: str,
        indicator: str,
        indicator_color: Optional[str],
    ) -> str:
        """Format a single format item with indicator and highlighting.

        Args:
            fmt: Format name (e.g., "PDF", "EPUB")
            indicator: Status indicator symbol
            indicator_color: Color name for indicator, or None

        Returns:
            Formatted string with markup
        """
        # Build format display: [indicator] format_name
        format_display = f"[{indicator}] {fmt}"

        # Apply highlighting if this is the selected format
        if fmt == self.selected_format:
            if indicator_color:
                return f"[{Colors.SELECTED} {indicator_color}]{format_display}[/{Colors.SELECTED} {indicator_color}]"
            else:
                return f"[{Colors.SELECTED}]{format_display}[/{Colors.SELECTED}]"
        else:
            if indicator_color:
                return f"[{indicator_color}]{format_display}[/{indicator_color}]"
            else:
                return format_display

    def _build_display_text(self) -> str:
        """Build the formatted display text with indicators."""
        format_parts = []
        for fmt in self.formats:
            indicator, indicator_color = self._get_status_indicator(fmt)
            format_text = self._format_single_item(fmt, indicator, indicator_color)
            format_parts.append(format_text)

        formats_str = " | ".join(format_parts)
        return (
            f"{self.item_number:{ITEM_NUMBER_WIDTH}d} | "
            f"{self.item_name[:MAX_ITEM_NAME_DISPLAY_LENGTH]:{MAX_ITEM_NAME_DISPLAY_LENGTH}s} | "
            f"{formats_str:{FORMAT_DISPLAY_WIDTH}s} | "
            f"{self.item_size:>{SIZE_DISPLAY_WIDTH}s}"
        )

    def update_display(self) -> None:
        """Update the display label with current state."""
        if self._display_label is not None:
            self._display_label.update(self._build_display_text())

    def watch_selected_format(
        self, old_value: Optional[str], new_value: Optional[str]
    ) -> None:
        """React to selected_format changes."""
        self.update_display()

    def cycle_format(self) -> None:
        """Cycle to the next format."""
        if not self.formats:
            return
        current_idx = (
            self.formats.index(self.selected_format)
            if self.selected_format in self.formats
            else 0
        )
        next_idx = (current_idx + 1) % len(self.formats)
        self.selected_format = self.formats[next_idx]  # Triggers reactive update


class BundleListScreen(Container):
    """Screen showing list of bundles."""

    BINDINGS = [
        Binding("enter", "select_bundle", "Select", show=True),
        Binding("q", "quit_app", "Quit", show=True),
    ]

    def __init__(self, download_manager: DownloadManager):
        super().__init__()
        self.download_manager = download_manager
        self.bundles = []

    def compose(self) -> ComposeResult:
        yield Static(
            "📚 Humble Bundle Library",
            classes="header-text",
            id=WidgetIds.SCREEN_HEADER,
        )
        yield Static("Loading bundles...", id=WidgetIds.STATUS_TEXT)
        yield ListView(id=WidgetIds.BUNDLE_LIST)

    def on_mount(self) -> None:
        """Load bundles when mounted."""
        self.load_bundles()

    @work(exclusive=True)
    async def load_bundles(self) -> None:
        """Load bundles in background."""
        try:
            # Get all bundles (fast, no details) - this is I/O, safe to run in worker
            bundles = get_bundles()

            # Update UI - safe in async worker on event loop
            self.bundles = bundles
            list_view = self.query_one(f"#{WidgetIds.BUNDLE_LIST}", ListView)
            list_view.clear()

            for bundle in self.bundles:
                list_view.append(BundleItem(bundle["key"], bundle["name"]))

            # Set focus to the list and position cursor on first bundle
            if self.bundles:
                list_view.index = 0
                list_view.focus()

            status = self.query_one(f"#{WidgetIds.STATUS_TEXT}", Static)
            status.update(
                f"Found {len(self.bundles)} bundles. Use ↑↓ to navigate, Enter to select."
            )

        except HumbleCLIError as e:
            # Wrap CLI error in APIError for consistent handling
            error = APIError(
                message=str(e),
                user_message="Failed to load bundles from Humble Bundle. Please check your connection.",
            )
            logging.error(f"Failed to load bundles: {e}")
            status = self.query_one(f"#{WidgetIds.STATUS_TEXT}", Static)
            status.update(f"[red]{error.user_message}[/red]")

    def select_bundle(self) -> None:
        """Select and post message for the currently highlighted bundle."""
        list_view = self.query_one(f"#{WidgetIds.BUNDLE_LIST}", ListView)
        if list_view.index is not None and list_view.index < len(self.bundles):
            selected_bundle = self.bundles[list_view.index]
            self.post_message(
                BundleSelected(selected_bundle["key"], selected_bundle["name"])
            )

    def action_select_bundle(self) -> None:
        """Handle bundle selection action."""
        self.select_bundle()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle ListView selection (Enter key)."""
        self.select_bundle()

    def action_quit_app(self) -> None:
        """Quit the application."""
        self.app.exit()


class BundleSelected(Message):
    """Message sent when a bundle is selected."""

    def __init__(self, bundle_key: str, bundle_name: str):
        super().__init__()
        self.bundle_key = bundle_key
        self.bundle_name = bundle_name


class BundleDetailsScreen(Container):
    """Screen showing bundle details and items."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("enter", "download_item", "Download", show=True),
        Binding("right", "cycle_format", "Next Format", show=True),
        Binding("left", "cycle_format", "Prev Format", show=True),
        Binding("q", "quit_app", "Quit", show=True),
    ]

    def __init__(self, download_manager: DownloadManager, config: AppConfig):
        super().__init__()
        self.download_manager = download_manager
        self.config = config
        self.bundle_key = ""
        self.bundle_name = ""
        self.bundle_data = None
        self._queue = DownloadQueue(max_concurrent=self.config.max_concurrent_downloads)

    def _safe_query_widget(
        self,
        widget_id: str,
        widget_type: type,
        default_action: Optional[callable] = None,
    ) -> Optional[any]:
        """Safely query for a widget, handling exceptions.

        Args:
            widget_id: Widget selector (e.g., "#details-status")
            widget_type: Expected widget type (e.g., Static, ListView)
            default_action: Optional callback if widget not found

        Returns:
            Widget instance if found, None otherwise
        """
        try:
            return self.query_one(widget_id, widget_type)
        except NoMatches:
            # Widget doesn't exist yet (screen not mounted)
            if default_action:
                default_action()
            return None
        except Exception as e:
            logging.error(f"Unexpected error querying widget '{widget_id}': {e}")
            return None

    def _all_formats_downloaded(self, item_row: ItemFormatRow) -> bool:
        """Check if all formats for an item have been downloaded.

        Args:
            item_row: Row to check

        Returns:
            True if all formats are downloaded, False otherwise
        """
        return all(item_row.format_status.get(fmt, False) for fmt in item_row.formats)

    def _format_queue_status(self) -> str:
        """Format the download queue status string.

        Returns:
            Formatted status string showing active and optionally queued downloads
        """
        stats = self._queue.get_stats()
        if stats.queued > 0:
            return (
                f"Active: {stats.active}/{stats.max_concurrent} | "
                f"Queued: {stats.queued}"
            )
        else:
            return f"Active Downloads: {stats.active}/{stats.max_concurrent}"

    def _format_items_info(self) -> str:
        """Format the items count information.

        Returns:
            String showing number of items, or empty string if no bundle data
        """
        if self.bundle_data and self.bundle_data["items"]:
            return f"{len(self.bundle_data['items'])} items"
        return ""

    def _format_navigation_help(self) -> str:
        """Format the navigation help text.

        Returns:
            Help text string
        """
        return (
            "Use ↑↓ to navigate, ←→ to change format, Enter to download, ESC to go back"
        )

    def update_download_counter(self) -> None:
        """Update status bar with active download count."""
        status = self._safe_query_widget(f"#{WidgetIds.DETAILS_STATUS}", Static)
        if status is None:
            return

        queue_status = self._format_queue_status()
        items_info = self._format_items_info()

        if items_info:
            nav_help = self._format_navigation_help()
            status.update(f"{items_info} | {queue_status} | {nav_help}")
        else:
            status.update(queue_status)

    def show_notification(self, message: str) -> None:
        """Show a notification that auto-clears after configured duration."""
        try:
            notif = self.query_one(f"#{WidgetIds.NOTIFICATION_AREA}", Static)
            notif.update(message)
            # Schedule clearing after duration using set_timer
            self.set_timer(
                self.config.notification_duration, lambda: self.clear_notification()
            )
        except NoMatches:
            # Notification widget doesn't exist (screen not mounted)
            return
        except Exception:
            logging.exception(f"Unexpected error showing notification: {message!r}")
            return

    def clear_notification(self) -> None:
        """Clear the notification area."""
        try:
            notif = self.query_one(f"#{WidgetIds.NOTIFICATION_AREA}", Static)
            notif.update("")
        except NoMatches:
            # Notification widget doesn't exist (screen not mounted)
            return
        except Exception:
            logging.exception("Unexpected error clearing notification")
            return

    def maybe_remove_item(self, item_row: ItemFormatRow) -> None:
        """Remove item from view if all formats are downloaded."""
        # Only remove if ALL formats for this item are downloaded
        if self._all_formats_downloaded(item_row):
            try:
                item_row.remove()
            except NoMatches:
                # Items list doesn't exist (view changed)
                return
            except Exception:
                logging.exception(
                    f"Unexpected error removing item: {item_row.item_name}"
                )
                return

    def compose(self) -> ComposeResult:
        yield Static("", classes="header-text", id=WidgetIds.BUNDLE_HEADER)
        yield Static("", id=WidgetIds.BUNDLE_METADATA)
        yield Static("", id=WidgetIds.NOTIFICATION_AREA, classes="notification")
        yield Static("Loading...", id=WidgetIds.DETAILS_STATUS)
        yield ListView(id=WidgetIds.ITEMS_LIST)

    def load_bundle(self, bundle_key: str, bundle_name: str) -> None:
        """Load bundle details."""
        self.bundle_key = bundle_key
        self.bundle_name = bundle_name

        # Update header
        header = self.query_one(f"#{WidgetIds.BUNDLE_HEADER}", Static)
        header.update(f"📦 {bundle_name}")

        # Show loading status
        status = self.query_one(f"#{WidgetIds.DETAILS_STATUS}", Static)
        status.update("Loading bundle details...")

        # Load details in background
        self.load_details()

    @work(exclusive=True)
    async def load_details(self) -> None:
        """Load bundle details in background."""
        try:
            # Get parsed bundle data with download status - this is I/O, safe to run in worker
            bundle_data = self.download_manager.get_bundle_items(self.bundle_key)

            # Update UI - safe in async worker on event loop
            self.bundle_data = bundle_data

            # Update metadata
            metadata = self.query_one(f"#{WidgetIds.BUNDLE_METADATA}", Static)
            meta_text = (
                f"Purchased: {self.bundle_data['purchased']} | "
                f"Amount: {self.bundle_data['amount']} | "
                f"Total Size: {self.bundle_data['total_size']}"
            )
            metadata.update(meta_text)

            # Update items list
            list_view = self.query_one(f"#{WidgetIds.ITEMS_LIST}", ListView)
            list_view.clear()

            if not self.bundle_data["items"]:
                # Check if there are keys to display
                if self.bundle_data.get("keys"):
                    # Show keys table
                    status = self.query_one(f"#{WidgetIds.DETAILS_STATUS}", Static)
                    status.update(
                        f"{len(self.bundle_data['keys'])} game keys in this bundle. "
                        "Visit https://www.humblebundle.com/home/keys to redeem. Press ESC to go back."
                    )

                    # Add header row for keys
                    header_text = f"{'#':>3} | {'Key Name':60s} | {'Redeemed':>10s}"
                    list_view.append(ListItem(Label(f"[bold]{header_text}[/bold]")))

                    # Add keys
                    for key in self.bundle_data["keys"]:
                        redeemed_str = (
                            f"{StatusSymbols.DOWNLOADED} Yes"
                            if key["redeemed"]
                            else "No"
                        )
                        redeemed_color = (
                            Colors.SUCCESS if key["redeemed"] else Colors.WARNING
                        )
                        key_text = f"{key['number']:3d} | {key['name'][:60]:60s} | [{redeemed_color}]{redeemed_str:>10s}[/{redeemed_color}]"
                        list_view.append(ListItem(Label(key_text)))

                    # Set focus and position on first key
                    list_view.index = 1
                    list_view.focus()
                else:
                    # No items and no keys
                    status = self.query_one(f"#{WidgetIds.DETAILS_STATUS}", Static)
                    status.update(
                        f"[{Colors.WARNING}]No items found in this bundle. Press ESC to go back.[/{Colors.WARNING}]"
                    )
                    # Set focus to the ListView so ESC key works (ListView can be focused even when empty)
                    list_view.focus()
                return

            # Add header row
            header_text = f"{'#':{ITEM_NUMBER_WIDTH}} | {'Item Name':{MAX_ITEM_NAME_DISPLAY_LENGTH}s} | {'Formats':{FORMAT_DISPLAY_WIDTH}s} | {'Size':>{SIZE_DISPLAY_WIDTH}s}"
            list_view.append(ListItem(Label(f"[bold]{header_text}[/bold]")))

            # Add items
            for item in self.bundle_data["items"]:
                list_view.append(
                    ItemFormatRow(
                        item_number=item["number"],
                        item_name=item["name"],
                        formats=item["formats"],
                        item_size=item["size"],
                        format_status=item["format_status"],
                    )
                )

            # Set focus to the list and position cursor on first item (skip header)
            list_view.index = 1
            list_view.focus()

            # Update status
            self.update_download_counter()

        except HumbleCLIError as e:
            # Wrap CLI error in APIError for consistent handling
            error = APIError(
                message=str(e),
                user_message="Failed to load bundle details from Humble Bundle. Please try again.",
            )
            logging.error(f"Failed to load bundle details: {e}")
            status = self.query_one("#details-status", Static)
            status.update(f"[red]{error.user_message}[/red]")

    def action_go_back(self) -> None:
        """Go back to bundle list."""
        self.post_message(GoBack())

    def action_cycle_format(self) -> None:
        """Cycle through formats for selected item."""
        list_view = self.query_one("#items-list", ListView)
        if list_view.index is not None and list_view.index > 0:  # Skip header row
            selected = list_view.children[list_view.index]
            if isinstance(selected, ItemFormatRow):
                selected.cycle_format()

    def download_selected_item(self) -> None:
        """Download the currently selected item format."""
        list_view = self.query_one("#items-list", ListView)
        if list_view.index is None or list_view.index == 0:  # Skip header row
            return

        selected = list_view.children[list_view.index]
        if not isinstance(selected, ItemFormatRow):
            return

        # Download in background
        self.download_format(selected)

    def action_download_item(self) -> None:
        """Handle download action."""
        self.download_selected_item()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle ListView selection (Enter key)."""
        # Check if this is from the items list
        try:
            list_view = self.query_one(f"#{WidgetIds.ITEMS_LIST}", ListView)
            if event.list_view == list_view:
                self.download_selected_item()
        except NoMatches:
            # Items list doesn't exist (wrong screen), ignore
            return
        except Exception:
            logging.exception("Unexpected error handling list view selection")
            return

    def _handle_download_queued(
        self, item_row: ItemFormatRow, selected_format: str
    ) -> None:
        """Handle download entering queued state.

        Updates queue state and UI to show item is queued for download.
        Thread-safe through DownloadQueue.

        Args:
            item_row: Row representing the item being queued
            selected_format: Format that was queued
        """
        self._queue.mark_queued()
        item_row.format_queued[selected_format] = True
        item_row.update_display()
        self.update_download_counter()

    def _handle_download_started(
        self, item_row: ItemFormatRow, selected_format: str
    ) -> None:
        """Handle download moving from queued to active state.

        Updates queue state and UI to show download is in progress.
        Thread-safe through DownloadQueue.

        Args:
            item_row: Row representing the item being downloaded
            selected_format: Format being downloaded
        """
        self._queue.mark_started()
        item_row.format_queued[selected_format] = False
        item_row.format_downloading[selected_format] = True
        item_row.update_display()
        self.update_download_counter()

    def _handle_download_success(
        self, item_row: ItemFormatRow, selected_format: str
    ) -> None:
        """Handle successful download completion.

        Updates UI to show download completed, shows notification,
        and schedules item removal if all formats downloaded.

        Args:
            item_row: Row representing the completed item
            selected_format: Format that was downloaded
        """
        item_row.format_status[selected_format] = True
        item_row.format_downloading[selected_format] = False
        item_row.update_display()

        self.show_notification(
            f"[{Colors.SUCCESS}]{StatusSymbols.DOWNLOADED} Downloaded: {item_row.item_name} ({selected_format})[/{Colors.SUCCESS}]",
        )

        # Schedule item removal if all formats downloaded
        self.set_timer(
            self.config.item_removal_delay, lambda: self.maybe_remove_item(item_row)
        )

    def _handle_download_failure(
        self, item_row: ItemFormatRow, selected_format: str
    ) -> None:
        """Handle download failure (download attempt returned False).

        Clears downloading state and shows failure notification.

        Args:
            item_row: Row representing the failed item
            selected_format: Format that failed to download
        """
        item_row.format_downloading[selected_format] = False
        item_row.update_display()

        self.show_notification(
            f"[{Colors.ERROR}]{StatusSymbols.FAILED} Failed: {item_row.item_name} ({selected_format})[/{Colors.ERROR}]",
        )

    def _handle_download_error(
        self,
        item_row: ItemFormatRow,
        selected_format: str,
        error: Exception,
    ) -> None:
        """Handle download exception.

        Clears downloading state and shows error notification with
        user-friendly message if available.

        Args:
            item_row: Row representing the item that errored
            selected_format: Format that errored
            error: Exception that occurred
        """
        item_row.format_downloading[selected_format] = False
        item_row.update_display()

        # Use user_message from HumbleToolsError if available
        if isinstance(error, HumbleToolsError):
            error_msg = error.user_message
        else:
            error_msg = str(error)

        self.show_notification(
            f"[{Colors.ERROR}]{StatusSymbols.FAILED} {error_msg}[/{Colors.ERROR}]",
        )

    def _handle_download_cleanup(self) -> None:
        """Handle download cleanup (always called in finally block).

        Marks download as completed and updates UI.
        Thread-safe through DownloadQueue.
        """
        self._queue.mark_completed()
        self.update_download_counter()

    @work(thread=True)
    def download_format(self, item_row: ItemFormatRow) -> None:
        """Download the selected format.

        This method runs in a worker thread (via @work(thread=True)).
        UI updates are dispatched back to the main thread using call_from_thread.

        Args:
            item_row: Row containing item and format information
        """
        selected_format = item_row.selected_format

        # Early returns for invalid states
        if selected_format is None:
            return
        if item_row.format_downloading.get(selected_format, False):
            return  # Already downloading
        if item_row.format_queued.get(selected_format, False):
            return  # Already queued
        if item_row.format_status.get(selected_format, False):
            return  # Already downloaded

        # Mark as queued
        self.app.call_from_thread(
            self._handle_download_queued,
            item_row,
            selected_format,
        )

        # Acquire download slot to enforce concurrency limit (blocks until available)
        self._queue.acquire()

        try:
            # Move from queued to downloading
            self.app.call_from_thread(
                self._handle_download_started,
                item_row,
                selected_format,
            )

            # Perform download - blocking I/O is OK in thread worker
            try:
                success = self.download_manager.download_item(
                    bundle_key=self.bundle_key,
                    item_number=item_row.item_number,
                    format_name=selected_format,
                    output_dir=self.config.output_dir,
                )
            except HumbleCLIError as e:
                # Wrap CLI errors in DownloadError
                raise DownloadError(
                    message=str(e),
                    user_message=f"Download failed for {item_row.item_name}. Please try again.",
                ) from e
            except (IOError, OSError) as e:
                # Wrap file I/O errors in DownloadError
                raise DownloadError(
                    message=str(e),
                    user_message=f"File error during download: {e}",
                ) from e

            # Handle result
            if success:
                self.app.call_from_thread(
                    self._handle_download_success,
                    item_row,
                    selected_format,
                )
            else:
                self.app.call_from_thread(
                    self._handle_download_failure,
                    item_row,
                    selected_format,
                )

        except Exception as e:
            # Handle exception
            self.app.call_from_thread(
                self._handle_download_error,
                item_row,
                selected_format,
                e,
            )

        finally:
            # Always cleanup and release download slot
            self.app.call_from_thread(self._handle_download_cleanup)
            self._queue.release()

    def action_quit_app(self) -> None:
        """Quit the application."""
        self.app.exit()


class GoBack(Message):
    """Message to go back to bundle list."""

    pass


class HumbleBundleTUI(App):
    """Main TUI application for Humble Bundle EPUB Manager."""

    CSS = """
    Screen {
        background: $surface;
    }
    
    .header-text {
        background: $primary;
        color: $text;
        padding: 1;
        text-align: center;
        text-style: bold;
    }
    
    #status-text, #details-status, #bundle-metadata {
        padding: 0 1;
        color: $text-muted;
    }
    
    .notification {
        padding: 0 1;
        color: $text;
        height: 1;
        border: solid $accent;
    }
    
    ListView {
        height: 1fr;
        margin: 1 2;
    }
    
    ListItem {
        padding: 0 1;
    }
    
    ListItem:hover {
        background: $accent;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__()
        self.config = config or AppConfig()
        self.tracker = DownloadTracker()
        self.download_manager = DownloadManager(self.tracker)

        # Screens
        self.bundle_list_screen = None
        self.bundle_details_screen = None
        self.current_screen = "list"

    def compose(self) -> ComposeResult:
        yield Header()
        # Mount both screens - start with bundle list visible
        self.bundle_list_screen = BundleListScreen(self.download_manager)
        self.bundle_details_screen = BundleDetailsScreen(
            self.download_manager, self.config
        )
        yield self.bundle_list_screen
        yield self.bundle_details_screen
        yield Footer()

    def on_mount(self) -> None:
        """Initialize screen visibility on mount."""
        # Hide details screen initially
        if self.bundle_details_screen:
            self.bundle_details_screen.display = False

    def on_bundle_selected(self, message: BundleSelected) -> None:
        """Handle bundle selection."""
        # Hide bundle list, show details
        if self.bundle_list_screen:
            self.bundle_list_screen.display = False
        if self.bundle_details_screen:
            self.bundle_details_screen.display = True
            self.bundle_details_screen.load_bundle(
                message.bundle_key, message.bundle_name
            )

        self.current_screen = "details"

    def on_go_back(self, message: GoBack) -> None:
        """Handle going back to bundle list."""
        # Hide details, show bundle list
        if self.bundle_details_screen:
            self.bundle_details_screen.display = False
        if self.bundle_list_screen:
            self.bundle_list_screen.display = True
            # Restore focus to the bundle list
            list_view = self.bundle_list_screen.query_one(
                f"#{WidgetIds.BUNDLE_LIST}", ListView
            )
            list_view.focus()

        self.current_screen = "list"


def run_tui(output_dir: Optional[Path] = None, config: Optional[AppConfig] = None):
    """Run the TUI application.

    Args:
        output_dir: Output directory (deprecated, use config instead)
        config: Application configuration
    """
    if config is None:
        if output_dir is not None:
            # Support legacy output_dir parameter
            config = AppConfig(output_dir=output_dir)
        else:
            config = AppConfig()

    app = HumbleBundleTUI(config=config)
    app.run()
