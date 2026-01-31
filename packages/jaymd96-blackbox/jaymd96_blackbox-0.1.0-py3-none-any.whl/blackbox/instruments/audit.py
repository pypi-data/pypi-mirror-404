"""
Audit hook instrumentation using sys.addaudithook (PEP 578).

Captures:
- File opens (open, io.open)
- Socket connections (socket.connect)
- Subprocess creation (subprocess.Popen)
- Module imports (import)
- Code execution (exec, compile)
"""

import sys
import os
from typing import Any, Callable

from ..collector import get_collector, BreadcrumbType


# Track if hooks are installed
_audit_hook_installed = False
_audit_hook_func: Callable | None = None


# Events we care about
AUDIT_EVENTS = {
    # File operations
    'open': ('FILE', 'open'),
    'io.open': ('FILE', 'open'),

    # Socket operations
    'socket.connect': ('SOCKET', 'connect'),
    'socket.bind': ('SOCKET', 'bind'),
    'socket.sendto': ('SOCKET', 'sendto'),
    'socket.getaddrinfo': ('SOCKET', 'getaddrinfo'),

    # Subprocess
    'subprocess.Popen': ('SUBPROCESS', 'exec'),
    'os.system': ('SUBPROCESS', 'system'),
    'os.spawn': ('SUBPROCESS', 'spawn'),

    # Import
    'import': ('IMPORT', 'import'),

    # Execution (optional, can be noisy)
    # 'exec': ('EXEC', 'exec'),
    # 'compile': ('EXEC', 'compile'),
}


def _format_file_args(args: tuple) -> tuple[str, dict]:
    """Format file open arguments."""
    if not args:
        return "open(?)", {}

    path = args[0] if args else "?"
    mode = args[1] if len(args) > 1 else "r"

    # Shorten path for display
    if isinstance(path, (str, bytes, os.PathLike)):
        path_str = str(path)
        if len(path_str) > 50:
            path_str = "..." + path_str[-47:]
    else:
        path_str = str(path)

    return f"open({path_str}, mode={mode})", {"path": str(path), "mode": mode}


def _format_socket_args(event: str, args: tuple) -> tuple[str, dict]:
    """Format socket arguments."""
    if event == 'socket.connect':
        # args is typically (socket, address)
        if len(args) >= 2:
            addr = args[1]
            if isinstance(addr, tuple) and len(addr) >= 2:
                host, port = addr[0], addr[1]
                return f"connect({host}:{port})", {"host": host, "port": port}
        return f"connect({args})", {"raw": str(args)}

    elif event == 'socket.getaddrinfo':
        if args:
            host = args[0] if args else "?"
            return f"getaddrinfo({host})", {"host": str(host)}

    return f"{event}({args})", {"raw": str(args)}


def _format_subprocess_args(event: str, args: tuple) -> tuple[str, dict]:
    """Format subprocess arguments."""
    if event == 'subprocess.Popen':
        # args[0] is typically the command
        if args:
            cmd = args[0]
            if isinstance(cmd, (list, tuple)):
                cmd_str = ' '.join(str(c) for c in cmd[:5])
                if len(cmd) > 5:
                    cmd_str += " ..."
            else:
                cmd_str = str(cmd)[:100]
            return f"exec({cmd_str})", {"command": cmd}

    elif event == 'os.system':
        cmd = args[0] if args else "?"
        return f"system({cmd})", {"command": cmd}

    return f"{event}({args})", {"raw": str(args)}


def _format_import_args(args: tuple) -> tuple[str, dict]:
    """Format import arguments."""
    if args:
        module = args[0]
        return f"import {module}", {"module": module}
    return "import ?", {}


def _audit_hook(event: str, args: tuple) -> None:
    """Global audit hook that captures events."""
    if event not in AUDIT_EVENTS:
        return

    breadcrumb_type_str, category = AUDIT_EVENTS[event]
    breadcrumb_type = BreadcrumbType[breadcrumb_type_str]

    try:
        # Format based on event type
        if event in ('open', 'io.open'):
            message, data = _format_file_args(args)
        elif event.startswith('socket.'):
            message, data = _format_socket_args(event, args)
        elif event in ('subprocess.Popen', 'os.system', 'os.spawn'):
            message, data = _format_subprocess_args(event, args)
        elif event == 'import':
            message, data = _format_import_args(args)
        else:
            message = f"{event}({args})"
            data = {"raw": str(args)}

        # Add breadcrumb
        get_collector().add_breadcrumb(
            type=breadcrumb_type,
            category=category,
            message=message,
            data=data,
        )

    except Exception:
        # Never let the audit hook crash the program
        pass


def install_audit_hooks() -> None:
    """Install the audit hook for I/O tracking."""
    global _audit_hook_installed, _audit_hook_func

    if _audit_hook_installed:
        return

    _audit_hook_func = _audit_hook
    sys.addaudithook(_audit_hook_func)
    _audit_hook_installed = True


def uninstall_audit_hooks() -> None:
    """
    Mark audit hooks as uninstalled.

    Note: Python's audit hooks cannot actually be removed once installed.
    This just prevents future installation and disables the collector.
    """
    global _audit_hook_installed

    if _audit_hook_installed:
        # Can't actually remove, but we can disable the collector
        get_collector().disable()
        _audit_hook_installed = False


def is_audit_hooks_installed() -> bool:
    """Check if audit hooks are installed."""
    return _audit_hook_installed
