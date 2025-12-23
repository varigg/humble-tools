"""Main CLI entry point for Humble Bundle EPUB Manager."""

import functools
import sys
import traceback
from pathlib import Path

import click

from humble_tools import __version__
from humble_tools.core.display import (
    display_bundle_status,
    display_tracked_bundles_summary,
    print_error,
    print_info,
    print_success,
)
from humble_tools.core.download_manager import DownloadManager
from humble_tools.core.humble_wrapper import (
    HumbleCLIError,
    check_humble_cli,
    get_bundles,
)
from humble_tools.core.tracker import DownloadTracker


def handle_humble_cli_errors(func):
    """Decorator to handle HumbleCLIError consistently."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HumbleCLIError as e:
            print_error(str(e))
            sys.exit(1)

    return wrapper


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def main(ctx):
    """Humble Bundle EPUB Manager - Interactive TUI and download tracking for your bundles.

    Use 'hb-epub tui' to launch the interactive interface.
    For listing and downloading bundles, use humble-cli directly."""
    # Initialize shared objects - defer humble-cli check to individual commands
    ctx.ensure_object(dict)


def _ensure_initialized(ctx) -> None:
    """Ensure tracker and download_manager are initialized in context."""
    if "tracker" not in ctx.obj:
        if not check_humble_cli():
            print_error("humble-cli is not installed or not in PATH")
            print_info("Install from: https://github.com/tuxuser/humble-cli")
            sys.exit(1)
        ctx.obj["tracker"] = DownloadTracker()
        ctx.obj["download_manager"] = DownloadManager(ctx.obj["tracker"])


@main.command()
@click.argument("bundle_key", required=False)
@click.pass_context
@handle_humble_cli_errors
def status(ctx, bundle_key):
    """Show download progress for bundles.

    If BUNDLE_KEY is provided, shows detailed status for that bundle.
    Otherwise, shows summary table of all tracked bundles.
    """
    _ensure_initialized(ctx)
    download_manager = ctx.obj["download_manager"]
    tracker = ctx.obj["tracker"]

    if bundle_key:
        # Show status for specific bundle
        bundles = get_bundles()
        bundle_name = next(
            (b["name"] for b in bundles if b["key"].startswith(bundle_key)), bundle_key
        )

        stats = download_manager.get_bundle_stats(bundle_key)
        display_bundle_status(bundle_name, stats)
    else:
        # Show summary of all tracked bundles
        tracked_bundle_keys = tracker.get_tracked_bundles()

        if not tracked_bundle_keys:
            print_info("No downloads tracked yet. Use the TUI to download bundles.")
            return

        # Get bundle names from humble-cli (single call)
        try:
            all_bundles = get_bundles()
            bundle_names = {b["key"]: b["name"] for b in all_bundles}
        except HumbleCLIError:
            bundle_names = {}

        # Build list of bundles with stats
        bundles_with_stats = []
        for bundle_key in tracked_bundle_keys:
            stats = tracker.get_bundle_stats(bundle_key)
            bundles_with_stats.append(
                {
                    "key": bundle_key,
                    "name": bundle_names.get(bundle_key, bundle_key),
                    "downloaded": stats["downloaded"],
                    "total": stats["total"],
                }
            )

        display_tracked_bundles_summary(bundles_with_stats)


@main.command()
@click.argument("file_url")
@click.argument("bundle_key")
@click.argument("filename")
@click.pass_context
def mark_downloaded(ctx, file_url, bundle_key, filename):
    """Manually mark a file as downloaded."""
    _ensure_initialized(ctx)
    tracker = ctx.obj["tracker"]
    tracker.mark_downloaded(file_url, bundle_key, filename)
    print_success(f"Marked as downloaded: {filename}")


@main.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output directory (default: ~/Downloads/HumbleBundle)",
)
def tui(output):
    """Launch interactive TUI for browsing and downloading bundles."""
    # Check humble-cli first
    if not check_humble_cli():
        print_error("humble-cli is not installed or not in PATH")
        print_info("Install from: https://github.com/tuxuser/humble-cli")
        sys.exit(1)

    # Import here to avoid circular dependency
    from humble_tools.sync import main as sync_main

    # Set output directory
    if output is None:
        output_dir = Path.home() / "Downloads" / "HumbleBundle"
    else:
        output_dir = Path(output)

    # Run the TUI
    try:
        sync_main(output_dir=output_dir)
    except KeyboardInterrupt:
        print_info("\nExiting...")
    except Exception as e:
        print_error(f"Error running TUI: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
