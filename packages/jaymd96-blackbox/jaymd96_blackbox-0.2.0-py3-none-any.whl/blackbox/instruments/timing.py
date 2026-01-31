"""
Timing and performance metrics.

Captures:
- Function execution times
- Slow operation detection
- Call frequency tracking
"""

import time
import functools
import threading
from typing import Any, Callable
from contextlib import contextmanager

from ..collector import get_collector, TimingRecord


# Global state
_timing_enabled = True
_slow_threshold_ms = 100.0  # Default threshold for "slow" operations
_timing_lock = threading.Lock()


def set_slow_threshold(ms: float) -> None:
    """Set the threshold for slow operation detection."""
    global _slow_threshold_ms
    _slow_threshold_ms = ms


def get_slow_threshold() -> float:
    """Get the current slow threshold in milliseconds."""
    return _slow_threshold_ms


def enable_timing() -> None:
    """Enable timing collection."""
    global _timing_enabled
    _timing_enabled = True


def disable_timing() -> None:
    """Disable timing collection."""
    global _timing_enabled
    _timing_enabled = False


def is_timing_enabled() -> bool:
    """Check if timing is enabled."""
    return _timing_enabled


def _record_timing(
    name: str,
    duration_ms: float,
    category: str = "function",
    metadata: dict | None = None,
) -> None:
    """Record a timing measurement."""
    if not _timing_enabled:
        return

    is_slow = duration_ms >= _slow_threshold_ms

    record = TimingRecord(
        name=name,
        duration_ms=duration_ms,
        category=category,
        is_slow=is_slow,
        metadata=metadata or {},
    )

    get_collector().add_timing_record(record)


@contextmanager
def timed_block(name: str, category: str = "block"):
    """
    Context manager for timing a block of code.

    Usage:
        with timed_block("data_processing"):
            process_data()
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        _record_timing(name, duration_ms, category=category)


def timed(name: str | None = None, category: str = "function"):
    """
    Decorator for timing function execution.

    Usage:
        @timed()
        def my_function():
            pass

        @timed("custom_name", category="io")
        def another_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        func_name = name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                _record_timing(func_name, duration_ms, category=category)

        return wrapper
    return decorator


class TimingContext:
    """
    Manual timing context for more control.

    Usage:
        timer = TimingContext("operation")
        timer.start()
        # ... do work ...
        timer.stop()  # Records the timing
    """

    def __init__(self, name: str, category: str = "manual"):
        self.name = name
        self.category = category
        self._start_time: float | None = None
        self._duration_ms: float | None = None

    def start(self) -> "TimingContext":
        """Start the timer."""
        self._start_time = time.perf_counter()
        return self

    def stop(self, metadata: dict | None = None) -> float:
        """Stop the timer and record the measurement."""
        if self._start_time is None:
            return 0.0

        self._duration_ms = (time.perf_counter() - self._start_time) * 1000
        _record_timing(self.name, self._duration_ms, self.category, metadata)
        return self._duration_ms

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time without stopping."""
        if self._start_time is None:
            return 0.0
        if self._duration_ms is not None:
            return self._duration_ms
        return (time.perf_counter() - self._start_time) * 1000


# Auto-timing for common slow operations
def install_auto_timing() -> bool:
    """
    Install automatic timing for common slow operations.

    This patches time.sleep to track sleep durations.
    Returns True if installed successfully.
    """
    try:
        import time as time_module

        _original_sleep = time_module.sleep

        def timed_sleep(seconds):
            start = time.perf_counter()
            try:
                _original_sleep(seconds)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                _record_timing(
                    "time.sleep",
                    duration_ms,
                    category="sleep",
                    metadata={"requested_seconds": seconds},
                )

        time_module.sleep = timed_sleep
        return True

    except Exception:
        return False


def format_duration(ms: float) -> str:
    """Format duration in human-readable form."""
    if ms < 1:
        return f"{ms * 1000:.0f}μs"
    elif ms < 1000:
        return f"{ms:.1f}ms"
    elif ms < 60000:
        return f"{ms / 1000:.2f}s"
    else:
        minutes = int(ms // 60000)
        seconds = (ms % 60000) / 1000
        return f"{minutes}m {seconds:.1f}s"
