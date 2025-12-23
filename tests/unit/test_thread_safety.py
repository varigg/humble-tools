"""Unit tests for thread safety and concurrency.

Test Coverage:
- Thread-safe counter operations with locks
- Semaphore limiting of concurrent operations
- Configuration-driven semaphore initialization

Performance: Fast tests (< 0.1s each)
Dependencies: Uses BundleDetailsScreen and AppConfig
Note: Complex concurrency scenarios are tested in integration tests
"""

import random
import threading
from pathlib import Path
from unittest.mock import Mock

import pytest

from humble_tools.sync.app import BundleDetailsScreen
from humble_tools.sync.config import AppConfig


class TestBundleDetailsScreenThreadSafety:
    """Test thread safety of BundleDetailsScreen."""

    @pytest.fixture
    def mock_download_manager(self):
        """Create a mock epub manager."""
        manager = Mock()
        manager.get_bundle_items = Mock(
            return_value={
                "purchased": "2024-01-01",
                "amount": "$10.00",
                "total_size": "100 MB",
                "items": [],
                "keys": [],
            }
        )
        manager.download_item = Mock(return_value=True)
        return manager

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AppConfig(max_concurrent_downloads=3, output_dir=Path("/tmp/test"))

    @pytest.fixture
    def details_screen(self, mock_download_manager, config):
        """Create BundleDetailsScreen with mocked dependencies."""
        screen = BundleDetailsScreen(mock_download_manager, config)
        return screen

    def test_mixed_counter_operations_are_thread_safe(self, details_screen):
        """Test mixed increment/decrement counter operations with lock protection."""

        def increment():
            details_screen._queue.mark_queued()
            details_screen._queue.mark_started()

        def decrement():
            if details_screen._queue.active_count > 0:
                details_screen._queue.mark_completed()

        # Create mixed operations (20 increments, 15 decrements)
        threads = []
        for _ in range(20):
            threads.append(threading.Thread(target=increment))
        for _ in range(15):
            threads.append(threading.Thread(target=decrement))

        # Shuffle to simulate real concurrency
        random.shuffle(threads)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # With proper locking, value should be valid (no corruption)
        # Result depends on execution order, but should be >= 0 and <= 20
        assert 0 <= details_screen._queue.active_count <= 20

    def test_semaphore_limits_concurrent_access(self, mock_download_manager):
        """Test semaphore correctly limits concurrent operations to config value."""
        config = AppConfig(max_concurrent_downloads=2)
        screen = BundleDetailsScreen(mock_download_manager, config)

        max_concurrent = screen.config.max_concurrent_downloads

        # Acquire all available semaphore slots
        acquired = []
        for _ in range(max_concurrent):
            acquired.append(screen._queue.acquire(blocking=False))

        # All should succeed
        assert all(acquired)

        # Next acquire should fail (semaphore at capacity)
        assert screen._queue.acquire(blocking=False) is False

        # Release all slots
        for _ in range(max_concurrent):
            screen._queue.release()

        # Should be able to acquire again
        assert screen._queue.acquire(blocking=False) is True
        screen._queue.release()

    def test_semaphore_initialized_from_config(self, mock_download_manager):
        """Test semaphore uses max_concurrent_downloads from config."""
        config = AppConfig(max_concurrent_downloads=5)
        screen = BundleDetailsScreen(mock_download_manager, config)

        # Queue should be initialized with config value
        assert screen._queue.max_concurrent == 5

        # Test with different value
        config2 = AppConfig(max_concurrent_downloads=10)
        screen2 = BundleDetailsScreen(mock_download_manager, config2)
        assert screen2._queue.max_concurrent == 10
