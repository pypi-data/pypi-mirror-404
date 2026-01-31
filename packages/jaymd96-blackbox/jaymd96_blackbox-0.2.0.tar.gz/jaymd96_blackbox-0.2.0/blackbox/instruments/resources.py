"""
Resource monitoring using psutil.

Captures:
- Memory usage (RSS, VMS, percent)
- CPU usage
- Open files
- Network connections
- Thread count
"""

import os
import threading
import time
from typing import Callable

from ..collector import get_collector, ResourceSnapshot


# Track if psutil is available
_psutil_available = False
try:
    import psutil
    _psutil_available = True
except ImportError:
    psutil = None


# Background monitor thread
_monitor_thread: threading.Thread | None = None
_monitor_stop_event: threading.Event | None = None


def is_psutil_available() -> bool:
    """Check if psutil is available."""
    return _psutil_available


def capture_resource_snapshot() -> ResourceSnapshot | None:
    """
    Capture current resource state.

    Returns None if psutil is not available.
    """
    if not _psutil_available:
        return None

    try:
        process = psutil.Process(os.getpid())

        # Memory info
        mem_info = process.memory_info()
        mem_percent = process.memory_percent()

        # CPU (requires interval for accurate reading, so we use cached)
        try:
            cpu_percent = process.cpu_percent(interval=None)
        except Exception:
            cpu_percent = None

        # Open files
        try:
            open_files = [f.path for f in process.open_files()]
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            open_files = []

        # Network connections
        try:
            connections = []
            for conn in process.connections():
                conn_info = {
                    "type": conn.type.name if hasattr(conn.type, 'name') else str(conn.type),
                    "status": conn.status,
                }
                if conn.laddr:
                    conn_info["local"] = f"{conn.laddr.ip}:{conn.laddr.port}"
                if conn.raddr:
                    conn_info["remote"] = f"{conn.raddr.ip}:{conn.raddr.port}"
                connections.append(conn_info)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            connections = []

        # Thread count
        try:
            thread_count = process.num_threads()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            thread_count = None

        snapshot = ResourceSnapshot(
            timestamp=time.time(),
            memory_percent=mem_percent,
            memory_rss=mem_info.rss,
            memory_vms=mem_info.vms,
            cpu_percent=cpu_percent,
            open_files=open_files,
            connections=connections,
            thread_count=thread_count,
        )

        # Add to collector
        get_collector().add_resource_snapshot(snapshot)

        return snapshot

    except Exception:
        return None


def _monitor_loop(interval: float, stop_event: threading.Event) -> None:
    """Background monitoring loop."""
    while not stop_event.is_set():
        capture_resource_snapshot()
        stop_event.wait(interval)


def start_resource_monitor(interval: float = 1.0) -> bool:
    """
    Start background resource monitoring.

    Args:
        interval: Seconds between snapshots

    Returns:
        True if started, False if psutil not available
    """
    global _monitor_thread, _monitor_stop_event

    if not _psutil_available:
        return False

    if _monitor_thread is not None and _monitor_thread.is_alive():
        return True  # Already running

    _monitor_stop_event = threading.Event()
    _monitor_thread = threading.Thread(
        target=_monitor_loop,
        args=(interval, _monitor_stop_event),
        daemon=True,
        name="blackbox-resource-monitor",
    )
    _monitor_thread.start()

    return True


def stop_resource_monitor() -> None:
    """Stop background resource monitoring."""
    global _monitor_thread, _monitor_stop_event

    if _monitor_stop_event is not None:
        _monitor_stop_event.set()

    if _monitor_thread is not None:
        _monitor_thread.join(timeout=2.0)
        _monitor_thread = None
        _monitor_stop_event = None


def format_bytes(size: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size) < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def get_system_info() -> dict | None:
    """Get general system information."""
    if not _psutil_available:
        return None

    try:
        return {
            "cpu_count": psutil.cpu_count(),
            "total_memory": format_bytes(psutil.virtual_memory().total),
            "available_memory": format_bytes(psutil.virtual_memory().available),
            "platform": os.name,
        }
    except Exception:
        return None
