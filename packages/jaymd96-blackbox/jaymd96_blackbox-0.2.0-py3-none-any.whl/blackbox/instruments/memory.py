"""
Memory tracking using tracemalloc.

Captures:
- Top memory allocations by file/line
- Memory growth over time
- Potential leak detection
"""

import tracemalloc
import linecache
from typing import Callable

from ..collector import get_collector, MemoryAllocation


# Track state
_tracking_started = False
_baseline_snapshot: tracemalloc.Snapshot | None = None


def start_memory_tracking(nframe: int = 25) -> None:
    """
    Start tracking memory allocations.

    Args:
        nframe: Number of frames to capture in tracebacks
    """
    global _tracking_started, _baseline_snapshot

    if _tracking_started:
        return

    tracemalloc.start(nframe)
    _tracking_started = True

    # Take baseline snapshot
    _baseline_snapshot = tracemalloc.take_snapshot()


def stop_memory_tracking() -> None:
    """Stop tracking memory allocations."""
    global _tracking_started, _baseline_snapshot

    if not _tracking_started:
        return

    tracemalloc.stop()
    _tracking_started = False
    _baseline_snapshot = None


def is_memory_tracking_active() -> bool:
    """Check if memory tracking is active."""
    return _tracking_started


def get_top_allocations(
    limit: int = 10,
    key_type: str = "lineno",
    cumulative: bool = False,
) -> list[MemoryAllocation]:
    """
    Get top memory allocations.

    Args:
        limit: Number of top allocations to return
        key_type: How to group allocations ("lineno", "filename", "traceback")
        cumulative: If True, include child allocations

    Returns:
        List of MemoryAllocation objects
    """
    if not _tracking_started:
        return []

    try:
        snapshot = tracemalloc.take_snapshot()

        # Filter out tracemalloc and blackbox internals
        snapshot = snapshot.filter_traces([
            tracemalloc.Filter(False, tracemalloc.__file__),
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
            tracemalloc.Filter(False, "*blackbox*"),
        ])

        # Get statistics
        stats = snapshot.statistics(key_type, cumulative=cumulative)

        allocations = []
        for stat in stats[:limit]:
            frame = stat.traceback[0] if stat.traceback else None

            allocation = MemoryAllocation(
                filename=frame.filename if frame else "?",
                lineno=frame.lineno if frame else 0,
                size=stat.size,
                count=stat.count,
            )
            allocations.append(allocation)

        # Update collector
        get_collector().set_memory_allocations(allocations)

        return allocations

    except Exception:
        return []


def get_memory_diff() -> list[MemoryAllocation]:
    """
    Get memory difference since tracking started.

    Returns allocations that have grown since the baseline.
    """
    global _baseline_snapshot

    if not _tracking_started or _baseline_snapshot is None:
        return []

    try:
        current = tracemalloc.take_snapshot()

        # Compare with baseline
        diff = current.compare_to(_baseline_snapshot, "lineno")

        allocations = []
        for stat in diff[:20]:  # Top 20 diffs
            if stat.size_diff > 0:  # Only growing allocations
                frame = stat.traceback[0] if stat.traceback else None

                allocation = MemoryAllocation(
                    filename=frame.filename if frame else "?",
                    lineno=frame.lineno if frame else 0,
                    size=stat.size_diff,
                    count=stat.count_diff,
                )
                allocations.append(allocation)

        return allocations

    except Exception:
        return []


def get_memory_usage() -> dict:
    """Get current tracemalloc memory usage."""
    if not _tracking_started:
        return {"tracked": False}

    try:
        current, peak = tracemalloc.get_traced_memory()
        return {
            "tracked": True,
            "current": current,
            "peak": peak,
            "current_formatted": format_size(current),
            "peak_formatted": format_size(peak),
        }
    except Exception:
        return {"tracked": False}


def format_size(size: int) -> str:
    """Format size in bytes to human readable."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(size) < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def get_allocation_traceback(
    filename: str,
    lineno: int,
    limit: int = 5,
) -> list[str] | None:
    """
    Get the traceback for allocations at a specific location.

    Returns formatted traceback lines.
    """
    if not _tracking_started:
        return None

    try:
        snapshot = tracemalloc.take_snapshot()
        stats = snapshot.statistics("traceback")

        for stat in stats:
            if stat.traceback:
                frame = stat.traceback[0]
                if frame.filename == filename and frame.lineno == lineno:
                    lines = []
                    for frame in stat.traceback[:limit]:
                        line = linecache.getline(frame.filename, frame.lineno).strip()
                        lines.append(f"  {frame.filename}:{frame.lineno}: {line}")
                    return lines

        return None

    except Exception:
        return None
