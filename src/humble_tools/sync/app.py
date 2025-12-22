"""Textual-based TUI for Humble Bundle EPUB Manager."""

import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.message import Message
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

from humble_tools.core.download_manager import DownloadManager
from humble_tools.core.humble_wrapper import HumbleCLIError, get_bundles
from humble_tools.core.tracker import DownloadTracker


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
        self.selected_format = selected_format or (formats[0] if formats else None)
        self.format_downloading: Dict[
            str, bool
        ] = {}  # Track which formats are downloading
        self.format_queued: Dict[
            str, bool
        ] = {}  # Track which formats are queued

    def compose(self) -> ComposeResult:
        # Build format string with download indicators
        format_parts = []
        for fmt in self.formats:
            # Check download status: queued > downloading > downloaded > not downloaded
            if self.format_queued.get(fmt, False):
                indicator = "🕒"  # Queued
                indicator_color = "blue"
            elif self.format_downloading.get(fmt, False):
                indicator = "⏳"  # Downloading
                indicator_color = "yellow"
            elif self.format_status.get(fmt, False):
                indicator = "✓"  # Downloaded
                indicator_color = "green"
            else:
                indicator = " "  # Not downloaded
                indicator_color = None

            # Highlight selected format
            if fmt == self.selected_format:
                if indicator_color:
                    format_parts.append(
                        f"[bold cyan {indicator_color}][{indicator}] {fmt}[/bold cyan {indicator_color}]"
                    )
                else:
                    format_parts.append(f"[bold cyan][{indicator}] {fmt}[/bold cyan]")
            else:
                if indicator_color:
                    format_parts.append(
                        f"[{indicator_color}][{indicator}] {fmt}[/{indicator_color}]"
                    )
                else:
                    format_parts.append(f"[{indicator}] {fmt}")

        formats_str = " | ".join(format_parts)

        # Create the display text
        text = f"{self.item_number:3d} | {self.item_name[:50]:50s} | {formats_str:30s} | {self.item_size:>10s}"
        yield Label(text)

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
        self.selected_format = self.formats[next_idx]
        # Refresh display
        self.remove_children()
        self.mount(*self.compose())


class BundleListScreen(Container):
    """Screen showing list of bundles."""

    BINDINGS = [
        Binding("enter", "select_bundle", "Select", show=True),
        Binding("q", "quit_app", "Quit", show=True),
    ]

    def __init__(self, epub_manager: DownloadManager):
        super().__init__()
        self.epub_manager = epub_manager
        self.bundles = []

    def compose(self) -> ComposeResult:
        yield Static(
            "📚 Humble Bundle Library", classes="header-text", id="screen-header"
        )
        yield Static("Loading bundles...", id="status-text")
        yield ListView(id="bundle-list")

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
            list_view = self.query_one("#bundle-list", ListView)
            list_view.clear()

            for bundle in self.bundles:
                list_view.append(BundleItem(bundle["key"], bundle["name"]))

            # Set focus to the list and position cursor on first bundle
            if self.bundles:
                list_view.index = 0
                list_view.focus()

            status = self.query_one("#status-text", Static)
            status.update(
                f"Found {len(self.bundles)} bundles. Use ↑↓ to navigate, Enter to select."
            )

        except HumbleCLIError as e:
            status = self.query_one("#status-text", Static)
            status.update(f"[red]Error loading bundles: {e}[/red]")

    def action_select_bundle(self) -> None:
        """Handle bundle selection."""
        list_view = self.query_one("#bundle-list", ListView)
        if list_view.index is not None and list_view.index < len(self.bundles):
            selected_bundle = self.bundles[list_view.index]
            self.post_message(
                BundleSelected(selected_bundle["key"], selected_bundle["name"])
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle ListView selection (Enter key)."""
        list_view = self.query_one("#bundle-list", ListView)
        if list_view.index is not None and list_view.index < len(self.bundles):
            selected_bundle = self.bundles[list_view.index]
            self.post_message(
                BundleSelected(selected_bundle["key"], selected_bundle["name"])
            )

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

    def __init__(self, epub_manager: DownloadManager, output_dir: Path):
        super().__init__()
        self.epub_manager = epub_manager
        self.output_dir = output_dir
        self.bundle_key = ""
        self.bundle_name = ""
        self.bundle_data = None
        self.active_downloads = 0  # Track number of active downloads
        self.queued_downloads = 0  # Track number of queued downloads
        self.max_concurrent_downloads = 3  # Configurable limit (default 3)
        self._download_semaphore = threading.Semaphore(self.max_concurrent_downloads)

    def update_download_counter(self) -> None:
        """Update status bar with active download count."""
        try:
            status = self.query_one("#details-status", Static)
        except Exception:
            # Status widget might not exist yet
            return
            
        if self.queued_downloads > 0:
            queue_info = (
                f"Active: {self.active_downloads}/{self.max_concurrent_downloads} | Queued: {self.queued_downloads}"
            )
        else:
            queue_info = (
                f"Active Downloads: {self.active_downloads}/{self.max_concurrent_downloads}"
            )

        if self.bundle_data and self.bundle_data["items"]:
            items_info = f"{len(self.bundle_data['items'])} items"
            nav_info = "Use ↑↓ to navigate, ←→ to change format, Enter to download, ESC to go back"
            status.update(f"{items_info} | {queue_info} | {nav_info}")
        else:
            status.update(queue_info)

    def show_notification(self, message: str, duration: int = 5) -> None:
        """Show a notification that auto-clears after duration."""
        try:
            notif = self.query_one("#notification-area", Static)
            notif.update(message)
            # Schedule clearing after duration using set_timer
            self.set_timer(duration, lambda: self.clear_notification())
        except Exception:
            # If notification widget doesn't exist, skip
            pass

    def clear_notification(self) -> None:
        """Clear the notification area."""
        try:
            notif = self.query_one("#notification-area", Static)
            notif.update("")
        except Exception:
            # If notification widget doesn't exist, skip
            pass

    def maybe_remove_item(self, item_row: ItemFormatRow) -> None:
        """Remove item from view if all formats are downloaded."""
        # Only remove if ALL formats for this item are downloaded
        if all(item_row.format_status.values()):
            try:
                list_view = self.query_one("#items-list", ListView)
                item_row.remove()
            except Exception:
                # Item already removed or view changed
                pass

    def compose(self) -> ComposeResult:
        yield Static("", classes="header-text", id="bundle-header")
        yield Static("", id="bundle-metadata")
        yield Static("", id="notification-area", classes="notification")
        yield Static("Loading...", id="details-status")
        yield ListView(id="items-list")

    def load_bundle(self, bundle_key: str, bundle_name: str) -> None:
        """Load bundle details."""
        self.bundle_key = bundle_key
        self.bundle_name = bundle_name

        # Update header
        header = self.query_one("#bundle-header", Static)
        header.update(f"📦 {bundle_name}")

        # Show loading status
        status = self.query_one("#details-status", Static)
        status.update("Loading bundle details...")

        # Load details in background
        self.load_details()

    @work(exclusive=True)
    async def load_details(self) -> None:
        """Load bundle details in background."""
        try:
            # Get parsed bundle data with download status - this is I/O, safe to run in worker
            bundle_data = self.epub_manager.get_bundle_items(self.bundle_key)
            
            # Update UI - safe in async worker on event loop
            self.bundle_data = bundle_data
            
            # Update metadata
            metadata = self.query_one("#bundle-metadata", Static)
            meta_text = (
                f"Purchased: {self.bundle_data['purchased']} | "
                f"Amount: {self.bundle_data['amount']} | "
                f"Total Size: {self.bundle_data['total_size']}"
            )
            metadata.update(meta_text)

            # Update items list
            list_view = self.query_one("#items-list", ListView)
            list_view.clear()

            if not self.bundle_data["items"]:
                # Check if there are keys to display
                if self.bundle_data.get("keys"):
                    # Show keys table
                    status = self.query_one("#details-status", Static)
                    status.update(
                        f"{len(self.bundle_data['keys'])} game keys in this bundle. "
                        "Visit https://www.humblebundle.com/home/keys to redeem. Press ESC to go back."
                    )

                    # Add header row for keys
                    header_text = f"{'#':>3} | {'Key Name':60s} | {'Redeemed':>10s}"
                    list_view.append(ListItem(Label(f"[bold]{header_text}[/bold]")))

                    # Add keys
                    for key in self.bundle_data["keys"]:
                        redeemed_str = "✓ Yes" if key["redeemed"] else "No"
                        redeemed_color = "green" if key["redeemed"] else "yellow"
                        key_text = f"{key['number']:3d} | {key['name'][:60]:60s} | [{redeemed_color}]{redeemed_str:>10s}[/{redeemed_color}]"
                        list_view.append(ListItem(Label(key_text)))

                    # Set focus and position on first key
                    list_view.index = 1
                    list_view.focus()
                else:
                    # No items and no keys
                    status = self.query_one("#details-status", Static)
                    status.update(
                        "[yellow]No items found in this bundle. Press ESC to go back.[/yellow]"
                    )
                    # Set focus to the ListView so ESC key works (ListView can be focused even when empty)
                    list_view.focus()
                return

            # Add header row
            header_text = (
                f"{'#':>3} | {'Item Name':50s} | {'Formats':30s} | {'Size':>10s}"
            )
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
            status = self.query_one("#details-status", Static)
            status.update(f"[red]Error loading details: {e}[/red]")

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

    def action_download_item(self) -> None:
        """Download selected item format."""
        list_view = self.query_one("#items-list", ListView)
        if list_view.index is None or list_view.index == 0:  # Skip header row
            return

        selected = list_view.children[list_view.index]
        if not isinstance(selected, ItemFormatRow):
            return

        # Download in background
        self.download_format(selected)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle ListView selection (Enter key) - delegate to bundle list if needed."""
        # Check if this is from the items list
        try:
            list_view = self.query_one("#items-list", ListView)
            if event.list_view == list_view:
                # This is from our items list
                if list_view.index is None or list_view.index == 0:  # Skip header row
                    return

                selected = list_view.children[list_view.index]
                if not isinstance(selected, ItemFormatRow):
                    return

                # Download in background
                self.download_format(selected)
        except Exception:
            # Not our list view, ignore
            pass

    @work(thread=True)
    async def download_format(self, item_row: ItemFormatRow) -> None:
        """Download the selected format."""
        selected_format = item_row.selected_format
        
        # Early return if no format selected
        if selected_format is None:
            return
        
        # Check if already downloading or downloaded
        if item_row.format_downloading.get(selected_format, False):
            return  # Already downloading
        if item_row.format_queued.get(selected_format, False):
            return  # Already queued
        if item_row.format_status.get(selected_format, False):
            return  # Already downloaded
        
        # Show queued state - use call_from_thread since we're in a worker thread
        def mark_queued():
            self.queued_downloads += 1
            item_row.format_queued[selected_format] = True
            item_row.remove_children()
            item_row.mount(*item_row.compose())
            self.update_download_counter()
        
        self.app.call_from_thread(mark_queued)
        
        # Acquire semaphore to enforce concurrency limit (blocks until available)
        self._download_semaphore.acquire()
        try:
            # Now move from queued to downloading
            def start_downloading():
                self.queued_downloads -= 1
                self.active_downloads += 1
                item_row.format_queued[selected_format] = False
                item_row.format_downloading[selected_format] = True
                item_row.remove_children()
                item_row.mount(*item_row.compose())
                self.update_download_counter()
            
            self.app.call_from_thread(start_downloading)

            # Perform download - blocking I/O is OK in thread worker
            success = self.epub_manager.download_item(
                    bundle_key=self.bundle_key,
                    item_number=item_row.item_number,
                    format_name=selected_format,
                    output_dir=self.output_dir,
                )

            if success:
                # Update UI from thread
                def on_success():
                    item_row.format_status[selected_format] = True
                    item_row.format_downloading[selected_format] = False
                    item_row.remove_children()
                    item_row.mount(*item_row.compose())
                    self.show_notification(
                        f"[green]✓ Downloaded: {item_row.item_name} ({selected_format})[/green]",
                        duration=5,
                    )
                    # Schedule item removal if all formats downloaded
                    self.set_timer(10, lambda: self.maybe_remove_item(item_row))
                
                self.app.call_from_thread(on_success)
            else:
                # Handle failure
                def on_failure():
                    item_row.format_downloading[selected_format] = False
                    item_row.remove_children()
                    item_row.mount(*item_row.compose())
                    self.show_notification(
                        f"[red]✗ Failed: {item_row.item_name} ({selected_format})[/red]",
                        duration=5,
                    )
                
                self.app.call_from_thread(on_failure)
                
        except Exception as e:
            # Handle exception
            def on_error():
                item_row.format_downloading[selected_format] = False
                item_row.remove_children()
                item_row.mount(*item_row.compose())
                self.show_notification(f"[red]Error: {e}[/red]", duration=5)
            
            self.app.call_from_thread(on_error)
        finally:
            # Always decrement counter and release semaphore
            def cleanup():
                self.active_downloads -= 1
                self.update_download_counter()
            
            self.app.call_from_thread(cleanup)
            self._download_semaphore.release()

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

    def __init__(self, output_dir: Optional[Path] = None):
        super().__init__()
        self.tracker = DownloadTracker()
        self.epub_manager = DownloadManager(self.tracker)
        self.output_dir = output_dir or (Path.home() / "Downloads" / "HumbleBundle")

        # Screens
        self.bundle_list_screen = None
        self.bundle_details_screen = None
        self.current_screen = "list"

    def compose(self) -> ComposeResult:
        yield Header()
        # Mount both screens - start with bundle list visible
        self.bundle_list_screen = BundleListScreen(self.epub_manager)
        self.bundle_details_screen = BundleDetailsScreen(
            self.epub_manager, self.output_dir
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
            list_view = self.bundle_list_screen.query_one("#bundle-list", ListView)
            list_view.focus()

        self.current_screen = "list"


def run_tui(output_dir: Optional[Path] = None):
    """Run the TUI application."""
    app = HumbleBundleTUI(output_dir=output_dir)
    app.run()
