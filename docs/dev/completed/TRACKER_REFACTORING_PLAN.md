# DownloadTracker Dependency Injection Refactoring Plan

**Date:** December 22, 2025  
**Status:** Planning  
**Priority:** Medium (Improves testability and design)

## Problem Statement

The current `DownloadTracker` implementation has tight coupling to SQLite file-based storage:

1. **Hard to test:** Cannot easily use in-memory databases because:

   - Tracker creates its own database connection
   - Constructor calls `db_path.parent.mkdir()` which fails for `:memory:` strings
   - Each method opens/closes connections, making it hard to share a connection

2. **Violates Single Responsibility Principle:** Tracker is responsible for:

   - Database path management
   - Directory creation
   - Connection management
   - Schema initialization
   - Business logic (tracking downloads)

3. **Limited flexibility:** Cannot easily:
   - Mock the database for testing
   - Use different database backends
   - Share connections across operations
   - Use connection pools

## Proposed Solution: Dependency Injection

Inject a database connection (or connection factory) into the tracker, separating concerns:

- **Database Management:** External responsibility (app/test setup)
- **Tracker:** Business logic only (tracking downloads)

## Refactoring Approach

### Option A: Inject Connection (Recommended)

**Pros:**

- Clean separation of concerns
- Easy to test with in-memory databases
- Supports connection pooling
- No breaking changes to existing API

**Cons:**

- Slightly more complex initialization
- Need to manage connection lifecycle externally

### Option B: Inject Connection Factory

**Pros:**

- More flexible (can create connections as needed)
- Supports connection pooling naturally

**Cons:**

- More complex API
- Still need to manage factory lifecycle

**Recommendation:** Use Option A with a backward-compatible wrapper.

---

## Implementation Plan

### Phase 1: Create New Implementation (Non-Breaking)

#### Step 1: Create DatabaseConnection Protocol

**File:** `src/humble_tools/core/database.py` (new)

```python
"""Database abstraction for download tracking."""

import sqlite3
from pathlib import Path
from typing import Protocol, Optional


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
    """SQLite database connection wrapper."""

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


def create_default_connection(db_path: Optional[Path] = None) -> SQLiteConnection:
    """Create default SQLite connection with proper path handling.

    Args:
        db_path: Path to database file. Defaults to ~/.humblebundle/downloads.db

    Returns:
        Configured SQLite connection
    """
    if db_path is None:
        db_path = Path.home() / ".humblebundle" / "downloads.db"

    # Create parent directories for file-based databases
    if db_path != Path(":memory:") and str(db_path) != ":memory:":
        db_path.parent.mkdir(parents=True, exist_ok=True)

    return SQLiteConnection(db_path)
```

#### Step 2: Refactor DownloadTracker

**File:** `src/humble_tools/core/tracker.py`

```python
"""SQLite-based download tracking for Humble Bundle files."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from humble_tools.core.database import DatabaseConnection, create_default_connection


class DownloadTracker:
    """Track downloaded files in a database."""

    def __init__(
        self,
        db_connection: Optional[DatabaseConnection] = None,
        db_path: Optional[Path] = None  # Deprecated, kept for compatibility
    ):
        """Initialize the download tracker.

        Args:
            db_connection: Database connection. Takes precedence over db_path.
            db_path: DEPRECATED. Path to SQLite database. Use db_connection instead.
                    Defaults to ~/.humblebundle/downloads.db
        """
        if db_connection is not None:
            self._conn = db_connection
            self._owns_connection = False
        else:
            # Backward compatibility: create connection from path
            self._conn = create_default_connection(db_path)
            self._owns_connection = True

    def close(self):
        """Close database connection if we own it."""
        if self._owns_connection and hasattr(self._conn, 'close'):
            self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def mark_downloaded(
        self,
        file_url: str,
        bundle_key: str,
        filename: str,
        file_path: Optional[str] = None,
        file_size: Optional[str] = None,
        bundle_total_files: Optional[int] = None,
    ):
        """Mark a file as downloaded."""
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
        """Check if a file has been downloaded."""
        cursor = self._conn.execute(
            "SELECT 1 FROM downloads WHERE file_url = ?", (file_url,)
        )
        return cursor.fetchone() is not None

    def get_bundle_stats(self, bundle_key: str) -> Dict[str, Optional[int]]:
        """Get download statistics for a bundle."""
        cursor = self._conn.execute(
            "SELECT COUNT(*), MAX(bundle_total_files) FROM downloads WHERE bundle_key = ?",
            (bundle_key,),
        )
        result = cursor.fetchone()
        downloaded = result[0]
        total_files = result[1]

        if total_files is None:
            return {"downloaded": downloaded, "remaining": None, "total": None}

        return {
            "downloaded": downloaded,
            "remaining": max(0, total_files - downloaded),
            "total": total_files,
        }

    def get_all_stats(self) -> Dict[str, int]:
        """Get overall download statistics."""
        cursor = self._conn.execute("SELECT COUNT(*) FROM downloads")
        total = cursor.fetchone()[0]
        return {"total_downloaded": total}

    def get_tracked_bundles(self) -> List[str]:
        """Get list of bundle keys that have tracked downloads."""
        cursor = self._conn.execute(
            "SELECT DISTINCT bundle_key FROM downloads ORDER BY bundle_key"
        )
        return [row[0] for row in cursor.fetchall()]

    def get_downloaded_files(
        self, bundle_key: Optional[str] = None
    ) -> List[Tuple[str, str, str]]:
        """Get list of downloaded files."""
        if bundle_key:
            cursor = self._conn.execute(
                "SELECT filename, bundle_key, downloaded_at FROM downloads WHERE bundle_key = ?",
                (bundle_key,),
            )
        else:
            cursor = self._conn.execute(
                "SELECT filename, bundle_key, downloaded_at FROM downloads"
            )
        return cursor.fetchall()
```

#### Step 3: Update Tests

**File:** `tests/conftest.py`

```python
from humble_tools.core.database import SQLiteConnection

@pytest.fixture
def mock_tracker():
    """Create a mock tracker for testing."""
    return Mock()


@pytest.fixture
def memory_db():
    """Create in-memory database connection."""
    return SQLiteConnection(":memory:")


@pytest.fixture
def temp_db():
    """Create temporary file-based database connection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = SQLiteConnection(db_path)
        yield conn
        conn.close()


@pytest.fixture
def fast_tracker(memory_db):
    """In-memory tracker for fast tests."""
    return DownloadTracker(db_connection=memory_db)


@pytest.fixture
def temp_tracker(temp_db):
    """Temporary file-based tracker."""
    return DownloadTracker(db_connection=temp_db)


# Backward compatibility
@pytest.fixture
def epub_manager(mock_tracker):
    """Create a DownloadManager with a mock tracker."""
    return DownloadManager(tracker=mock_tracker)
```

---

### Phase 2: Migration (Breaking Changes Allowed)

#### Option 1: Keep Backward Compatibility (Recommended for libraries)

- Keep `db_path` parameter with deprecation warning
- Update all internal usage to use `db_connection`
- Document migration path in changelog

#### Option 2: Clean Break (If major version bump acceptable)

- Remove `db_path` parameter entirely
- Require `db_connection` parameter
- Update all calling code simultaneously

---

## Migration Guide for Existing Code

### Before (Current):

```python
# Default location
tracker = DownloadTracker()

# Custom location
tracker = DownloadTracker(db_path=Path("/custom/path.db"))

# In tests (doesn't work properly)
tracker = DownloadTracker(db_path=":memory:")
```

### After (New):

```python
from humble_tools.core.database import create_default_connection, SQLiteConnection

# Default location (unchanged)
tracker = DownloadTracker()  # Still works via backward compatibility

# Custom location
conn = create_default_connection(Path("/custom/path.db"))
tracker = DownloadTracker(db_connection=conn)

# In tests (now works properly!)
conn = SQLiteConnection(":memory:")
tracker = DownloadTracker(db_connection=conn)
```

---

## Testing Strategy

### Unit Tests to Add:

1. `test_database.py`:

   - Test `SQLiteConnection` initialization
   - Test schema creation
   - Test in-memory database
   - Test file-based database
   - Test connection lifecycle

2. Update `test_tracker.py`:
   - Use `fast_tracker` fixture (in-memory)
   - Verify all operations work with injected connection
   - Test backward compatibility with `db_path`

### Integration Tests:

1. Verify app works with new implementation
2. Test connection sharing across components
3. Verify no regressions in production usage

---

## Rollout Plan

### Step 1: Add New Code (Week 1)

- [ ] Create `database.py` module
- [ ] Add tests for database module
- [ ] Update tracker to accept both parameters
- [ ] Add deprecation warning for `db_path`

### Step 2: Update Internal Usage (Week 1-2)

- [ ] Update `DownloadManager`
- [ ] Update `HumbleBundleTUI`
- [ ] Update track commands
- [ ] Update all test fixtures

### Step 3: Verify & Document (Week 2)

- [ ] Run full test suite
- [ ] Update documentation
- [ ] Add migration guide
- [ ] Create changelog entry

### Step 4: Deprecation (Future Release)

- [ ] Add console warnings for `db_path` usage
- [ ] Update all examples in docs
- [ ] Plan removal date (e.g., 6 months)

---

## Benefits After Refactoring

### Testability

- ✅ In-memory databases work properly
- ✅ Fast test execution (no file I/O)
- ✅ Easy to mock database for unit tests
- ✅ No more directory creation issues

### Design

- ✅ Single Responsibility Principle
- ✅ Dependency Injection pattern
- ✅ Easier to extend (new database backends)
- ✅ Better separation of concerns

### Performance

- ✅ Can share connections across operations
- ✅ Connection pooling support
- ✅ Reduced file system overhead in tests

---

## Risks and Mitigations

### Risk 1: Breaking Changes

**Mitigation:** Keep `db_path` parameter with deprecation warning for 1-2 releases

### Risk 2: Increased Complexity

**Mitigation:** Provide helper functions like `create_default_connection()` for common cases

### Risk 3: Migration Effort

**Mitigation:**

- Backward compatibility ensures existing code works
- Clear migration guide and examples
- Gradual rollout over multiple releases

---

## Alternative Approaches Considered

### 1. Keep Current Design, Fix mkdir Issue

**Pros:** Minimal changes
**Cons:** Doesn't address root cause, still tightly coupled

### 2. Use SQLAlchemy or ORM

**Pros:** More abstraction, better features
**Cons:** Heavy dependency, overkill for simple use case

### 3. Abstract Storage Layer (Repository Pattern)

**Pros:** Ultimate flexibility
**Cons:** Too complex for current needs, over-engineering

**Decision:** Go with dependency injection (Option A) - best balance of simplicity and flexibility.

---

## Success Criteria

- [ ] All existing tests pass
- [ ] Fast tracker using in-memory DB works in tests
- [ ] No regressions in production usage
- [ ] Test execution time improves by >30%
- [ ] Code coverage maintained or improved
- [ ] Documentation updated
- [ ] Migration guide published
