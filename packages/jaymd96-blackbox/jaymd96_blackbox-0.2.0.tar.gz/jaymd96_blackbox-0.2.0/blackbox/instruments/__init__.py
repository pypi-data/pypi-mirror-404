"""
Instrumentation modules for blackbox.

Each module provides hooks into different aspects of Python execution:
- audit: sys.addaudithook for file/socket/subprocess events
- resources: psutil for system resource monitoring
- memory: tracemalloc for memory allocation tracking
- http: wrapt for HTTP request instrumentation
- database: SQLAlchemy and generic DB logging
- environment: Environment variable access tracking
- timing: Function timing and slow operation detection
"""

from .audit import (
    install_audit_hooks,
    uninstall_audit_hooks,
    is_audit_hooks_installed,
)
from .resources import (
    capture_resource_snapshot,
    start_resource_monitor,
    stop_resource_monitor,
    is_psutil_available,
    get_system_info,
)
from .memory import (
    start_memory_tracking,
    stop_memory_tracking,
    get_top_allocations,
    get_memory_diff,
    get_memory_usage,
    is_memory_tracking_active,
)
from .http import (
    install_http_hooks,
    uninstall_http_hooks,
    is_http_hooks_installed,
    is_wrapt_available,
)
from .database import (
    install_database_hooks,
    install_sqlalchemy_hooks,
    install_sqlite3_hooks,
    is_sqlalchemy_hooks_installed,
)
from .environment import (
    install_env_hooks,
    uninstall_env_hooks,
    is_env_hooks_installed,
    get_env_snapshot,
)
from .timing import (
    timed,
    timed_block,
    TimingContext,
    set_slow_threshold,
    get_slow_threshold,
    enable_timing,
    disable_timing,
    is_timing_enabled,
    install_auto_timing,
    format_duration,
)


def install_all_hooks() -> dict[str, bool]:
    """
    Install all available instrumentation hooks.

    Returns dict of hook name -> success status.
    """
    results = {}

    # Audit hooks (always available via stdlib)
    try:
        install_audit_hooks()
        results["audit"] = True
    except Exception:
        results["audit"] = False

    # HTTP hooks (requires wrapt)
    results["http"] = install_http_hooks()

    # Database hooks
    db_results = install_database_hooks()
    results["sqlalchemy"] = db_results.get("sqlalchemy", False)
    results["sqlite3"] = db_results.get("sqlite3", False)

    # Environment hooks
    results["environment"] = install_env_hooks()

    # Auto-timing
    results["auto_timing"] = install_auto_timing()

    # Memory tracking
    try:
        start_memory_tracking()
        results["memory"] = True
    except Exception:
        results["memory"] = False

    # Resource monitoring (requires psutil)
    results["resources"] = start_resource_monitor(interval=1.0)

    return results


def uninstall_all_hooks() -> None:
    """Uninstall all instrumentation hooks."""
    uninstall_audit_hooks()
    uninstall_http_hooks()
    uninstall_env_hooks()
    stop_memory_tracking()
    stop_resource_monitor()
    disable_timing()


__all__ = [
    # All-in-one
    "install_all_hooks",
    "uninstall_all_hooks",
    # Audit hooks
    "install_audit_hooks",
    "uninstall_audit_hooks",
    "is_audit_hooks_installed",
    # Resources
    "capture_resource_snapshot",
    "start_resource_monitor",
    "stop_resource_monitor",
    "is_psutil_available",
    "get_system_info",
    # Memory
    "start_memory_tracking",
    "stop_memory_tracking",
    "get_top_allocations",
    "get_memory_diff",
    "get_memory_usage",
    "is_memory_tracking_active",
    # HTTP
    "install_http_hooks",
    "uninstall_http_hooks",
    "is_http_hooks_installed",
    "is_wrapt_available",
    # Database
    "install_database_hooks",
    "install_sqlalchemy_hooks",
    "install_sqlite3_hooks",
    "is_sqlalchemy_hooks_installed",
    # Environment
    "install_env_hooks",
    "uninstall_env_hooks",
    "is_env_hooks_installed",
    "get_env_snapshot",
    # Timing
    "timed",
    "timed_block",
    "TimingContext",
    "set_slow_threshold",
    "get_slow_threshold",
    "enable_timing",
    "disable_timing",
    "is_timing_enabled",
    "install_auto_timing",
    "format_duration",
]
