"""
Blackbox: LLM-Friendly Python Debugging

A debugging tool that provides structured, readable output
when Python code crashes, hangs, or behaves unexpectedly.

Features:
- Clean crash reports with local variables and code context
- I/O breadcrumb trail (file, socket, subprocess, HTTP, DB)
- Resource monitoring (memory, CPU, files, connections)
- Memory allocation tracking
- Timing and slow operation detection
- Automatic analysis hints

Usage:
    python -m blackbox script.py
    python -m blackbox --trace script.py
    python -m blackbox --focus mypackage script.py

Programmatic usage:
    from blackbox import install_crash_handler
    from blackbox.instruments import install_all_hooks

    install_all_hooks()
    install_crash_handler(focus=['mypackage'])
"""

__version__ = "0.1.0"

from .crash import install_crash_handler, CrashHandler
from .formatter import Formatter
from .filters import Filter
from .collector import get_collector, Collector, BreadcrumbType

__all__ = [
    "install_crash_handler",
    "CrashHandler",
    "Formatter",
    "Filter",
    "get_collector",
    "Collector",
    "BreadcrumbType",
]
