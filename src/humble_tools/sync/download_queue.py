"""Download queue management with thread-safe concurrency control.

This module provides a simple, thread-safe download queue manager that
controls concurrent downloads using a semaphore and tracks queue state
with atomic counter operations.
"""

import threading
from dataclasses import dataclass
from typing import Optional


@dataclass
class QueueStats:
    """Download queue statistics snapshot.

    Provides a consistent snapshot of the queue state at a point in time.
    All values are captured atomically.

    Attributes:
        active: Number of currently active downloads
        queued: Number of downloads waiting in queue
        max_concurrent: Maximum allowed concurrent downloads
    """

    active: int
    queued: int
    max_concurrent: int


class DownloadQueue:
    """Thread-safe download queue manager.

    Manages concurrent download queue with configurable limits.
    All operations are thread-safe through internal locking.

    The queue uses a semaphore to control concurrency and ensures
    that counter updates are atomic through a separate lock.

    Typical usage:
        >>> queue = DownloadQueue(max_concurrent=3)
        >>> queue.mark_queued()  # Add to queue
        >>> queue.acquire()      # Wait for available slot
        >>> queue.mark_started() # Move to active
        >>> try:
        ...     # Perform download
        ...     queue.mark_completed()
        ... finally:
        ...     queue.release()

    Thread Safety:
        All public methods are thread-safe and can be called from
        multiple threads simultaneously.

    Attributes:
        max_concurrent: Maximum number of simultaneous downloads allowed
    """

    def __init__(self, max_concurrent: int = 3) -> None:
        """Initialize download queue.

        Args:
            max_concurrent: Maximum simultaneous downloads (1-10)

        Raises:
            ValueError: If max_concurrent is not in valid range
        """
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        if max_concurrent > 10:
            raise ValueError("max_concurrent should not exceed 10")

        self.max_concurrent = max_concurrent
        self._semaphore = threading.Semaphore(max_concurrent)
        self._lock = threading.Lock()
        self._active = 0
        self._queued = 0

    def mark_queued(self) -> None:
        """Mark a download as queued.

        Increments the queued counter. Should be called before
        attempting to acquire a download slot.

        Thread-safe.
        """
        with self._lock:
            self._queued += 1

    def mark_started(self) -> None:
        """Move download from queued to active state.

        Decrements queued counter and increments active counter.
        Should be called after successfully acquiring a slot.

        Thread-safe.

        Raises:
            RuntimeError: If called when no downloads are queued
        """
        with self._lock:
            if self._queued <= 0:
                raise RuntimeError("Cannot start download: nothing queued")
            self._queued -= 1
            self._active += 1

    def mark_completed(self) -> None:
        """Mark download as completed.

        Decrements the active counter. Should be called when
        download finishes successfully.

        Thread-safe.

        Raises:
            RuntimeError: If called when no downloads are active
        """
        with self._lock:
            if self._active <= 0:
                raise RuntimeError("Cannot complete download: nothing active")
            self._active -= 1

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """Acquire a download slot.

        Blocks until a slot is available (if blocking=True).
        Must be paired with a release() call.

        Args:
            blocking: If True, block until slot available
            timeout: Maximum seconds to wait (None = wait forever)

        Returns:
            True if slot acquired, False if timeout or non-blocking and unavailable

        Thread-safe.
        """
        return self._semaphore.acquire(blocking=blocking, timeout=timeout)

    def release(self) -> None:
        """Release a download slot.

        Should be called in a finally block to ensure slot is
        always released, even on error.

        Thread-safe.
        """
        self._semaphore.release()

    def get_stats(self) -> QueueStats:
        """Get current queue statistics.

        Returns a consistent snapshot of the current queue state.
        All values are captured atomically.

        Returns:
            QueueStats object with current counts

        Thread-safe.
        """
        with self._lock:
            return QueueStats(
                active=self._active,
                queued=self._queued,
                max_concurrent=self.max_concurrent,
            )

    @property
    def active_count(self) -> int:
        """Get number of active downloads.

        Returns:
            Current count of active downloads

        Thread-safe.
        """
        with self._lock:
            return self._active

    @property
    def queued_count(self) -> int:
        """Get number of queued downloads.

        Returns:
            Current count of queued downloads

        Thread-safe.
        """
        with self._lock:
            return self._queued

    def __repr__(self) -> str:
        """String representation of queue state."""
        stats = self.get_stats()
        return (
            f"DownloadQueue(active={stats.active}, "
            f"queued={stats.queued}, "
            f"max={stats.max_concurrent})"
        )
