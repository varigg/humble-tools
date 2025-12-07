"""Rich console output formatting for beautiful CLI display."""

from typing import Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

console = Console()


def display_bundles(bundles: List[Dict], with_stats: bool = False):
    """Display bundles in a formatted table.

    Args:
        bundles: List of bundle dictionaries with 'key', 'name', and optional 'stats'
        with_stats: Whether to include download statistics
    """
    if not bundles:
        console.print("[yellow]No bundles found.[/yellow]")
        return

    table = Table(
        title="Humble Bundle Library", show_header=True, header_style="bold magenta"
    )
    table.add_column("Bundle Key", style="cyan", no_wrap=True)
    table.add_column("Bundle Name", style="white")

    if with_stats:
        table.add_column("Downloaded", justify="right", style="green")
        table.add_column("Remaining", justify="right", style="yellow")
        table.add_column("Total", justify="right", style="blue")

    for bundle in bundles:
        row = [bundle["key"], bundle["name"]]

        if with_stats and "stats" in bundle:
            stats = bundle["stats"]
            row.extend(
                [
                    str(stats.get("downloaded", 0)),
                    str(stats.get("remaining", 0)),
                    str(stats.get("total", 0)),
                ]
            )

        table.add_row(*row)

    console.print(table)


def display_tracked_bundles_summary(bundles: List[Dict]):
    """Display summary of tracked bundles with download progress.

    Args:
        bundles: List of bundle dicts with 'key', 'name', 'downloaded', 'total'
    """
    if not bundles:
        console.print("[yellow]No downloads tracked yet.[/yellow]")
        return

    table = Table(
        title="Download Progress by Bundle",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Bundle Key", style="cyan", no_wrap=True)
    table.add_column("Bundle Name", style="white")
    table.add_column("Downloaded", justify="right", style="green")
    table.add_column("Total", justify="right", style="blue")
    table.add_column("Progress", justify="right", style="yellow")

    total_downloaded = 0
    total_files = 0

    for bundle in bundles:
        downloaded = bundle.get("downloaded", 0)
        total = bundle.get("total")

        total_downloaded += downloaded

        if total is not None and total > 0:
            total_files += total
            percentage = downloaded / total * 100
            progress = f"{percentage:.1f}%"
        elif total == 0:
            progress = "Empty"
        else:
            progress = "?"

        total_str = str(total) if total is not None else "?"

        table.add_row(
            bundle["key"], bundle["name"], str(downloaded), total_str, progress
        )

    # Add summary row
    table.add_section()
    overall_progress = ""
    if total_files > 0:
        overall_pct = total_downloaded / total_files * 100
        overall_progress = f"{overall_pct:.1f}%"

    table.add_row(
        "[bold]TOTAL[/bold]",
        "",
        f"[bold]{total_downloaded}[/bold]",
        f"[bold]{total_files}[/bold]" if total_files > 0 else "[bold]?[/bold]",
        f"[bold]{overall_progress}[/bold]",
    )

    console.print(table)


def display_bundle_status(bundle_name: str, stats: Dict):
    """Display download status for a bundle.

    Args:
        bundle_name: Name of the bundle
        stats: Statistics dictionary with 'downloaded', 'remaining', 'total'
    """
    downloaded = stats.get("downloaded", 0)
    total = stats.get("total")
    remaining = stats.get("remaining")

    # Handle empty bundles
    if total == 0:
        panel_content = f"""
[bold white]{bundle_name}[/bold white]

[dim]No downloadable files in this bundle[/dim]
"""
        console.print(
            Panel(panel_content.strip(), title="Bundle Status", border_style="blue")
        )
        return

    # Handle None values when total is unknown
    if total is not None and total > 0:
        percentage = downloaded / total * 100
        progress_text = Text()
        progress_text.append(f"{downloaded}/{total} files downloaded ", style="white")
        progress_text.append(f"({percentage:.1f}%)", style="cyan")
        show_full_stats = True
    else:
        # Total unknown, just show downloaded count
        percentage = 0
        progress_text = Text()
        progress_text.append(f"{downloaded} files downloaded ", style="white")
        progress_text.append("(total unknown)", style="dim")
        show_full_stats = False

    # Create panel with stats
    if show_full_stats:
        # Show full stats with progress bar
        panel_content = f"""
[bold white]{bundle_name}[/bold white]

[green]✓ Downloaded:[/green] {downloaded} files
[yellow]⧗ Remaining:[/yellow] {remaining} files
[blue]Σ Total:[/blue] {total} files

Progress: [cyan]{"█" * int(percentage / 2)}{"░" * (50 - int(percentage / 2))}[/cyan] {percentage:.1f}%
"""
    else:
        # Show minimal stats when total is unknown
        panel_content = f"""
[bold white]{bundle_name}[/bold white]

[green]✓ Downloaded:[/green] {downloaded} files
[dim]Total files: Unknown[/dim]
"""

    console.print(
        Panel(panel_content.strip(), title="Bundle Status", border_style="blue")
    )


def display_overall_stats(stats: Dict):
    """Display overall download statistics.

    Args:
        stats: Overall statistics dictionary
    """
    total = stats.get("total_downloaded", 0)

    panel_content = f"""
[bold cyan]Overall Download Statistics[/bold cyan]

[green]✓ Total Files Downloaded:[/green] {total}
"""

    console.print(
        Panel(panel_content.strip(), title="Download Tracker", border_style="green")
    )


def print_success(message: str):
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str):
    """Print an error message."""
    console.print(f"[red]✗[/red] {message}", style="bold red")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}", style="yellow")


def print_info(message: str):
    """Print an info message."""
    console.print(f"[blue]ℹ[/blue] {message}")


def create_progress_bar(description: str = "Downloading..."):
    """Create a progress bar for downloads.

    Args:
        description: Description text for the progress bar

    Returns:
        Rich Progress object
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )
