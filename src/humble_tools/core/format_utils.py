"""Common formatting utilities shared across CLI and TUI."""

from typing import Optional


class FormatUtils:
    """Shared formatting utilities."""

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Convert bytes to human-readable size.

        Args:
            size_bytes: Size in bytes

        Returns:
            Human-readable size string (e.g., "1.5 GB", "250 MB")
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    @staticmethod
    def format_download_progress(downloaded: int, total: Optional[int]) -> str:
        """Format download progress as a percentage or status.

        Args:
            downloaded: Number of items downloaded
            total: Total number of items, or None if unknown

        Returns:
            Formatted progress string (e.g., "75.0%", "5/?")
        """
        if total is None:
            return f"{downloaded}/?"
        if total == 0:
            return "0%"
        percentage = (downloaded / total) * 100
        return f"{percentage:.1f}%"

    @staticmethod
    def format_bundle_stats(downloaded: int, total: Optional[int]) -> str:
        """Format bundle statistics string.

        Args:
            downloaded: Number downloaded
            total: Total number or None

        Returns:
            Formatted string (e.g., "5/10", "5/?")
        """
        if total is None:
            return f"{downloaded}/?"
        return f"{downloaded}/{total}"

    @staticmethod
    def truncate_string(text: str, max_length: int) -> str:
        """Truncate string to max length with ellipsis.

        Args:
            text: String to truncate
            max_length: Maximum length (including ellipsis)

        Returns:
            Truncated string
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."
