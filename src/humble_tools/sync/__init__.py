"""Sync tool - TUI application for Humble Bundle downloads."""

from pathlib import Path
from typing import Optional

from humble_tools.sync.app import run_tui


def main(output_dir: Optional[Path] = None) -> None:
    """Entry point for humble-sync command."""
    run_tui(output_dir=output_dir)


if __name__ == "__main__":
    main()
