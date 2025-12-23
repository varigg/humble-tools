"""Unit tests for download queue management.

Test Coverage:
- State machine validation (queued→started→completed transitions)
- Error cases (invalid state transitions raise RuntimeError)
- Initialization validation (max_concurrent bounds)
- Statistics snapshot consistency
- Basic acquire/release operations
- Property accessors

Note: Thread safety and concurrent operations are covered by test_thread_safety.py
"""

import pytest
from humble_tools.sync.download_queue import DownloadQueue, QueueStats


class TestDownloadQueue:
    """Tests for DownloadQueue class."""

    def test_initialization_default(self):
        """Test default initialization."""
        queue = DownloadQueue()
        assert queue.max_concurrent == 3
        assert queue.active_count == 0
        assert queue.queued_count == 0

    def test_initialization_custom(self):
        """Test custom max_concurrent value."""
        queue = DownloadQueue(max_concurrent=5)
        assert queue.max_concurrent == 5
        assert queue.active_count == 0
        assert queue.queued_count == 0

    def test_initialization_validates_minimum(self):
        """Test initialization rejects values below minimum."""
        with pytest.raises(ValueError, match="must be at least 1"):
            DownloadQueue(max_concurrent=0)

        with pytest.raises(ValueError, match="must be at least 1"):
            DownloadQueue(max_concurrent=-5)

    def test_initialization_validates_maximum(self):
        """Test initialization rejects values above maximum."""
        with pytest.raises(ValueError, match="should not exceed 10"):
            DownloadQueue(max_concurrent=11)

        with pytest.raises(ValueError, match="should not exceed 10"):
            DownloadQueue(max_concurrent=100)

    def test_state_transition_happy_path(self):
        """Test normal state transition: queued→started→completed."""
        queue = DownloadQueue()

        # Initial state
        assert queue.queued_count == 0
        assert queue.active_count == 0

        # Mark as queued
        queue.mark_queued()
        assert queue.queued_count == 1
        assert queue.active_count == 0

        # Move to started
        queue.mark_started()
        assert queue.queued_count == 0
        assert queue.active_count == 1

        # Mark as completed
        queue.mark_completed()
        assert queue.queued_count == 0
        assert queue.active_count == 0

    def test_multiple_queued_items(self):
        """Test multiple items can be queued."""
        queue = DownloadQueue()

        queue.mark_queued()
        queue.mark_queued()
        queue.mark_queued()

        assert queue.queued_count == 3
        assert queue.active_count == 0

        queue.mark_started()
        assert queue.queued_count == 2
        assert queue.active_count == 1

    def test_mark_started_without_queued_raises(self):
        """Test that starting without queuing raises RuntimeError."""
        queue = DownloadQueue()

        with pytest.raises(RuntimeError, match="nothing queued"):
            queue.mark_started()

        # Verify state unchanged
        assert queue.queued_count == 0
        assert queue.active_count == 0

    def test_mark_completed_without_active_raises(self):
        """Test that completing without active raises RuntimeError."""
        queue = DownloadQueue()

        with pytest.raises(RuntimeError, match="nothing active"):
            queue.mark_completed()

        # Verify state unchanged
        assert queue.queued_count == 0
        assert queue.active_count == 0

    def test_get_stats_returns_consistent_snapshot(self):
        """Test that get_stats returns consistent snapshot."""
        queue = DownloadQueue(max_concurrent=5)

        queue.mark_queued()
        queue.mark_queued()
        queue.mark_started()

        stats = queue.get_stats()

        assert isinstance(stats, QueueStats)
        assert stats.active == 1
        assert stats.queued == 1
        assert stats.max_concurrent == 5

    def test_acquire_release_basic(self):
        """Test basic acquire and release operations."""
        queue = DownloadQueue(max_concurrent=2)

        # Acquire first slot
        assert queue.acquire(blocking=False) is True

        # Acquire second slot
        assert queue.acquire(blocking=False) is True

        # No more slots available
        assert queue.acquire(blocking=False) is False

        # Release one slot
        queue.release()

        # Slot available again
        assert queue.acquire(blocking=False) is True

        # Clean up
        queue.release()
        queue.release()

    def test_repr(self):
        """Test string representation."""
        queue = DownloadQueue(max_concurrent=3)
        queue.mark_queued()
        queue.mark_started()

        repr_str = repr(queue)

        assert "DownloadQueue" in repr_str
        assert "active=1" in repr_str
        assert "queued=0" in repr_str
        assert "max=3" in repr_str

    def test_properties_are_thread_safe_accessors(self):
        """Test that properties return correct values."""
        queue = DownloadQueue()

        assert queue.active_count == 0
        assert queue.queued_count == 0

        queue.mark_queued()
        assert queue.queued_count == 1

        queue.mark_started()
        assert queue.active_count == 1
        assert queue.queued_count == 0
