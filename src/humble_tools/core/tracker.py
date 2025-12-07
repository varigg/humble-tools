"""SQLite-based download tracking for Humble Bundle files."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DownloadTracker:
    """Track downloaded files in a SQLite database."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the download tracker.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.humblebundle/downloads.db
        """
        if db_path is None:
            db_path = Path.home() / ".humblebundle" / "downloads.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    file_url TEXT PRIMARY KEY,
                    bundle_key TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_size TEXT,
                    downloaded_at TIMESTAMP NOT NULL,
                    file_path TEXT,
                    bundle_total_files INTEGER
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_bundle_key 
                ON downloads(bundle_key)
            """)
            conn.commit()

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
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
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
            conn.commit()

    def is_downloaded(self, file_url: str) -> bool:
        """Check if a file has been downloaded.

        Args:
            file_url: Unique URL of the file

        Returns:
            True if file is in database, False otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM downloads WHERE file_url = ?", (file_url,)
            )
            return cursor.fetchone() is not None

    def get_bundle_stats(self, bundle_key: str) -> Dict[str, Optional[int]]:
        """Get download statistics for a bundle.

        Args:
            bundle_key: Bundle identifier

        Returns:
            Dictionary with 'downloaded', 'remaining', and 'total' counts
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get count and total from any download record for this bundle
            cursor = conn.execute(
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM downloads")
            total = cursor.fetchone()[0]

        return {"total_downloaded": total}

    def get_tracked_bundles(self) -> List[str]:
        """Get list of bundle keys that have tracked downloads.

        Returns:
            List of bundle keys
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT DISTINCT bundle_key FROM downloads ORDER BY bundle_key"
            )
            return [row[0] for row in cursor.fetchall()]

    def get_downloaded_files(
        self, bundle_key: Optional[str] = None
    ) -> List[Tuple[str, str, str]]:
        """Get list of downloaded files.

        Args:
            bundle_key: Optional bundle key to filter by

        Returns:
            List of tuples (filename, bundle_key, downloaded_at)
        """
        with sqlite3.connect(self.db_path) as conn:
            if bundle_key:
                cursor = conn.execute(
                    "SELECT filename, bundle_key, downloaded_at FROM downloads WHERE bundle_key = ?",
                    (bundle_key,),
                )
            else:
                cursor = conn.execute(
                    "SELECT filename, bundle_key, downloaded_at FROM downloads"
                )
            return cursor.fetchall()
