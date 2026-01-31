"""
Central collector for all instrumentation data.

Aggregates breadcrumbs, resource snapshots, memory info, and timing data
into a unified structure for the crash handler to use.
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Any
from collections import deque
from enum import Enum


class BreadcrumbType(Enum):
    """Types of breadcrumbs that can be recorded."""
    FILE = "FILE"
    HTTP = "HTTP"
    DB = "DB"
    SUBPROCESS = "SUBPROCESS"
    ENV = "ENV"
    SOCKET = "SOCKET"
    IMPORT = "IMPORT"
    CONFIG = "CONFIG"
    CUSTOM = "CUSTOM"


@dataclass
class Breadcrumb:
    """A single breadcrumb recording an I/O or significant event."""
    timestamp: float
    type: BreadcrumbType
    category: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    duration: float | None = None

    @property
    def relative_time(self) -> float:
        """Time relative to collector start."""
        return self.timestamp - _collector.start_time if _collector else 0.0


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time."""
    timestamp: float
    memory_percent: float | None = None
    memory_rss: int | None = None  # bytes
    memory_vms: int | None = None  # bytes
    cpu_percent: float | None = None
    open_files: list[str] = field(default_factory=list)
    connections: list[dict] = field(default_factory=list)
    thread_count: int | None = None


@dataclass
class MemoryAllocation:
    """Information about a memory allocation."""
    filename: str
    lineno: int
    size: int  # bytes
    count: int  # number of allocations


@dataclass
class TimingRecord:
    """Timing information for a function or operation."""
    name: str
    duration_ms: float
    category: str = "function"
    is_slow: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class Collector:
    """
    Central collector for all instrumentation data.

    Thread-safe collection of breadcrumbs, resources, memory, and timing.
    """

    def __init__(self, max_breadcrumbs: int = 100):
        self.max_breadcrumbs = max_breadcrumbs
        self.start_time = time.time()

        self._breadcrumbs: deque[Breadcrumb] = deque(maxlen=max_breadcrumbs)
        self._resource_snapshots: list[ResourceSnapshot] = []
        self._memory_allocations: list[MemoryAllocation] = []
        self._timing_records: list[TimingRecord] = []

        self._lock = threading.Lock()
        self._enabled = True

    def add_breadcrumb(
        self,
        type: BreadcrumbType,
        category: str,
        message: str,
        data: dict[str, Any] | None = None,
        duration: float | None = None,
    ) -> None:
        """Add a breadcrumb to the trail."""
        if not self._enabled:
            return

        breadcrumb = Breadcrumb(
            timestamp=time.time(),
            type=type,
            category=category,
            message=message,
            data=data or {},
            duration=duration,
        )

        with self._lock:
            self._breadcrumbs.append(breadcrumb)

    def add_resource_snapshot(self, snapshot: ResourceSnapshot) -> None:
        """Add a resource snapshot."""
        if not self._enabled:
            return

        with self._lock:
            self._resource_snapshots.append(snapshot)
            # Keep only last 10 snapshots
            if len(self._resource_snapshots) > 10:
                self._resource_snapshots = self._resource_snapshots[-10:]

    def set_memory_allocations(self, allocations: list[MemoryAllocation]) -> None:
        """Set the current top memory allocations."""
        if not self._enabled:
            return

        with self._lock:
            self._memory_allocations = allocations

    def add_timing_record(self, record: TimingRecord) -> None:
        """Add a timing record."""
        if not self._enabled:
            return

        with self._lock:
            self._timing_records.append(record)
            # Keep only last 50 timing records
            if len(self._timing_records) > 50:
                self._timing_records = self._timing_records[-50:]

    def get_breadcrumbs(self) -> list[Breadcrumb]:
        """Get all breadcrumbs."""
        with self._lock:
            return list(self._breadcrumbs)

    def get_latest_resource_snapshot(self) -> ResourceSnapshot | None:
        """Get the most recent resource snapshot."""
        with self._lock:
            return self._resource_snapshots[-1] if self._resource_snapshots else None

    def get_memory_allocations(self) -> list[MemoryAllocation]:
        """Get current memory allocations."""
        with self._lock:
            return list(self._memory_allocations)

    def get_timing_records(self) -> list[TimingRecord]:
        """Get timing records."""
        with self._lock:
            return list(self._timing_records)

    def get_slow_operations(self, threshold_ms: float = 100.0) -> list[TimingRecord]:
        """Get operations slower than threshold (in milliseconds)."""
        with self._lock:
            return [r for r in self._timing_records if r.is_slow]

    def clear(self) -> None:
        """Clear all collected data."""
        with self._lock:
            self._breadcrumbs.clear()
            self._resource_snapshots.clear()
            self._memory_allocations.clear()
            self._timing_records.clear()

    def disable(self) -> None:
        """Disable collection (for cleanup)."""
        self._enabled = False

    def enable(self) -> None:
        """Enable collection."""
        self._enabled = True


# Global collector instance
_collector: Collector | None = None


def get_collector() -> Collector:
    """Get or create the global collector."""
    global _collector
    if _collector is None:
        _collector = Collector()
    return _collector


def reset_collector() -> Collector:
    """Reset the global collector."""
    global _collector
    _collector = Collector()
    return _collector


# Convenience functions for adding breadcrumbs
def add_breadcrumb(
    type: BreadcrumbType,
    category: str,
    message: str,
    data: dict[str, Any] | None = None,
    duration: float | None = None,
) -> None:
    """Add a breadcrumb to the global collector."""
    get_collector().add_breadcrumb(type, category, message, data, duration)
