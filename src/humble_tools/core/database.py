"""Database abstraction for download tracking."""

import sqlite3
from pathlib import Path
from typing import Protocol

# Default database paths
DEFAULT_DATA_DIR = Path.home() / ".humblebundle"
DEFAULT_DATABASE_PATH = DEFAULT_DATA_DIR / "downloads.db"


class DatabaseConnection(Protocol):
    """Protocol for database connection interface."""

    def execute(self, sql: str, parameters=None):
        """Execute SQL statement."""
        ...

    def commit(self):
        """Commit transaction."""
        ...

    def cursor(self):
        """Get cursor for queries."""
        ...


class SQLiteConnection:
    """SQLite database connection wrapper with schema management."""

    def __init__(self, db_path: str | Path = ":memory:"):
        """Initialize SQLite connection.

        Args:
            db_path: Path to database file or ":memory:" for in-memory DB
        """
        if isinstance(db_path, Path):
            db_path = str(db_path)

        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._initialize_schema()

    def _initialize_schema(self):
        """Initialize the database schema."""
        self._conn.execute("""
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
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_bundle_key 
            ON downloads(bundle_key)
        """)
        self._conn.commit()

    def execute(self, sql: str, parameters=None):
        """Execute SQL statement."""
        if parameters:
            return self._conn.execute(sql, parameters)
        return self._conn.execute(sql)

    def commit(self):
        """Commit transaction."""
        self._conn.commit()

    def cursor(self):
        """Get cursor for queries."""
        return self._conn.cursor()

    def close(self):
        """Close connection."""
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        self.close()


def create_default_connection(db_path: Path | None = None) -> SQLiteConnection:
    """Create default SQLite connection with proper path handling.

    Args:
        db_path: Path to database file. Defaults to ~/.humblebundle/downloads.db

    Returns:
        Configured SQLite connection
    """
    if db_path is None:
        db_path = DEFAULT_DATABASE_PATH

    # Create parent directories for file-based databases
    if db_path != Path(":memory:") and str(db_path) != ":memory:":
        db_path.parent.mkdir(parents=True, exist_ok=True)

    return SQLiteConnection(db_path)
