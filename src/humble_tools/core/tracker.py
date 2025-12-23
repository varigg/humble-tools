"""SQLite-based download tracking for Humble Bundle files."""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from humble_tools.core.database import DatabaseConnection, create_default_connection


class DownloadTracker:
    """Track downloaded files in a database."""

    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """Initialize the download tracker.

        Args:
            db_connection: Database connection. If None, creates default connection.
        """
        if db_connection is None:
            db_connection = create_default_connection()

        self._conn = db_connection

    def mark_downloaded(
        self,
        file_url: str,
        bundle_key: str,
        filename: str,
        file_path: Optional[str] = None,
        file_size: Optional[str] = None,
        bundle_total_files: Optional[int] = None,
    ):
        """Mark a file as downloaded.

        Args:
            file_url: Unique URL of the file
            bundle_key: Bundle identifier
            filename: Name of the file
            file_path: Local path where file was saved
            file_size: Human-readable file size
            bundle_total_files: Total number of files in the bundle
        """
        self._conn.execute(
            """
            INSERT OR REPLACE INTO downloads
            (file_url, bundle_key, filename, file_size, downloaded_at, file_path, bundle_total_files)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_url,
                bundle_key,
                filename,
                file_size,
                datetime.now(),
                file_path,
                bundle_total_files,
            ),
        )
        self._conn.commit()

    def is_downloaded(self, file_url: str) -> bool:
        """Check if a file has been downloaded.

        Args:
            file_url: Unique URL of the file

        Returns:
            True if file is in database, False otherwise
        """
        cursor = self._conn.execute("SELECT 1 FROM downloads WHERE file_url = ?", (file_url,))
        return cursor.fetchone() is not None

    def get_bundle_stats(self, bundle_key: str) -> Dict[str, Optional[int]]:
        """Get download statistics for a bundle.

        Args:
            bundle_key: Bundle identifier

        Returns:
            Dictionary with 'downloaded', 'remaining', and 'total' counts
        """
        cursor = self._conn.execute(
            "SELECT COUNT(*), MAX(bundle_total_files) FROM downloads WHERE bundle_key = ?",
            (bundle_key,),
        )
        result = cursor.fetchone()
        downloaded = result[0]
        total_files = result[1]  # Will be None if no records or if not set

        if total_files is None:
            return {"downloaded": downloaded, "remaining": None, "total": None}

        return {
            "downloaded": downloaded,
            "remaining": max(0, total_files - downloaded),
            "total": total_files,
        }

    def get_all_stats(self) -> Dict[str, int]:
        """Get overall download statistics.

        Returns:
            Dictionary with total downloaded count
        """
        cursor = self._conn.execute("SELECT COUNT(*) FROM downloads")
        total = cursor.fetchone()[0]
        return {"total_downloaded": total}

    def get_tracked_bundles(self) -> List[str]:
        """Get list of bundle keys that have tracked downloads.

        Returns:
            List of bundle keys
        """
        cursor = self._conn.execute("SELECT DISTINCT bundle_key FROM downloads ORDER BY bundle_key")
        return [row[0] for row in cursor.fetchall()]

    def get_downloaded_files(self, bundle_key: Optional[str] = None) -> List[Tuple[str, str, str]]:
        """Get list of downloaded files.

        Args:
            bundle_key: Optional bundle key to filter by

        Returns:
            List of tuples (filename, bundle_key, downloaded_at)
        """
        if bundle_key:
            cursor = self._conn.execute(
                "SELECT filename, bundle_key, downloaded_at FROM downloads WHERE bundle_key = ?",
                (bundle_key,),
            )
        else:
            cursor = self._conn.execute("SELECT filename, bundle_key, downloaded_at FROM downloads")
        return cursor.fetchall()
