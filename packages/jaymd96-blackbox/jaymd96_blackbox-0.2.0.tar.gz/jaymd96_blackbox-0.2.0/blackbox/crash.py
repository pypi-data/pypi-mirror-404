"""
Crash handler that captures and formats exception information.

Installs a custom excepthook that:
- Captures full stack with locals
- Extracts code context
- Provides analysis hints
- Outputs clean, structured text
"""

import sys
import os
import traceback
import linecache
import inspect
from types import TracebackType, FrameType
from typing import Any

from .formatter import Formatter, FrameInfo
from .filters import Filter, filter_frames
from .collector import get_collector
from .instruments.memory import get_top_allocations, is_memory_tracking_active
from .instruments.resources import capture_resource_snapshot


class CrashHandler:
    """
    Handles uncaught exceptions with rich debugging output.

    Usage:
        handler = CrashHandler(focus=['mypackage'])
        handler.install()
    """

    def __init__(
        self,
        focus: list[str] | None = None,
        collapse: list[str] | None = None,
        show_stdlib: bool = False,
        max_depth: int | None = None,
        context_lines: int = 2,
        max_value_length: int = 200,
        output_file=None,
    ):
        self.filter = Filter(
            focus=focus or [],
            collapse=collapse or [],
            show_stdlib=show_stdlib,
            max_depth=max_depth,
        )
        self.formatter = Formatter(
            max_value_length=max_value_length,
            context_lines=context_lines,
        )
        self.output_file = output_file or sys.stderr
        self._original_excepthook = None

    def install(self):
        """Install as the global exception handler."""
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._handle_exception

    def uninstall(self):
        """Restore the original exception handler."""
        if self._original_excepthook:
            sys.excepthook = self._original_excepthook

    def _handle_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None
    ):
        """Handle an uncaught exception."""
        try:
            output = self.format_exception(exc_type, exc_value, exc_tb)
            print(output, file=self.output_file)
        except Exception as e:
            # Fallback to standard traceback if our formatting fails
            print(f"[blackbox formatting error: {e}]", file=sys.stderr)
            if self._original_excepthook:
                self._original_excepthook(exc_type, exc_value, exc_tb)
            else:
                traceback.print_exception(exc_type, exc_value, exc_tb)

    def format_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None
    ) -> str:
        """Format an exception with full context."""
        # Extract all frames
        raw_frames = self._extract_frames(exc_tb)

        # Filter frames
        filtered_frames, collapsed = filter_frames(
            [self._frame_to_dict(f) for f in raw_frames],
            self.filter
        )

        # Convert to FrameInfo objects
        frame_infos = []
        for i, frame_dict in enumerate(filtered_frames):
            is_crash = i == len(filtered_frames) - 1
            frame_infos.append(FrameInfo(
                filename=self._short_path(frame_dict['filename']),
                lineno=frame_dict['lineno'],
                function=frame_dict['function'],
                code_context=frame_dict.get('code_context'),
                locals=frame_dict.get('locals', {}),
                args=frame_dict.get('args'),
                is_crash_site=is_crash,
            ))

        # Build call chain
        call_chain = [f.function for f in frame_infos]

        # Generate analysis
        analysis = self._analyze_exception(exc_type, exc_value, frame_infos)

        # Gather instrumentation data from collector
        collector = get_collector()
        breadcrumbs = collector.get_breadcrumbs()
        timing_records = collector.get_timing_records()

        # Capture final resource snapshot
        resource_snapshot = capture_resource_snapshot()

        # Get memory allocations if tracking is active
        memory_allocations = None
        if is_memory_tracking_active():
            memory_allocations = get_top_allocations(limit=10)

        return self.formatter.format_crash(
            exc_type=exc_type,
            exc_value=exc_value,
            frames=frame_infos,
            call_chain=call_chain,
            collapsed=collapsed if collapsed else None,
            analysis=analysis,
            breadcrumbs=breadcrumbs if breadcrumbs else None,
            resource_snapshot=resource_snapshot,
            memory_allocations=memory_allocations,
            timing_records=timing_records if timing_records else None,
        )

    def _extract_frames(self, tb: TracebackType | None) -> list[FrameType]:
        """Extract all frames from a traceback."""
        frames = []
        current = tb
        while current is not None:
            frames.append(current.tb_frame)
            current = current.tb_next
        return frames

    def _frame_to_dict(self, frame: FrameType) -> dict:
        """Convert a frame to a dictionary with all relevant info."""
        code = frame.f_code
        lineno = frame.f_lineno
        filename = code.co_filename
        function = code.co_name

        # Get code context
        code_context = self._get_code_context(filename, lineno)

        # Get locals (excluding modules and functions)
        locals_dict = {}
        for name, value in frame.f_locals.items():
            if not inspect.ismodule(value) and not inspect.isfunction(value):
                locals_dict[name] = value

        # Try to identify arguments
        args = None
        try:
            arginfo = inspect.getargvalues(frame)
            args = {}
            for arg in arginfo.args:
                if arg in frame.f_locals:
                    args[arg] = frame.f_locals[arg]
            # Include *args and **kwargs
            if arginfo.varargs and arginfo.varargs in frame.f_locals:
                args[f'*{arginfo.varargs}'] = frame.f_locals[arginfo.varargs]
            if arginfo.keywords and arginfo.keywords in frame.f_locals:
                args[f'**{arginfo.keywords}'] = frame.f_locals[arginfo.keywords]
        except Exception:
            pass

        # Try to get module name
        module = frame.f_globals.get('__name__')

        return {
            'filename': filename,
            'lineno': lineno,
            'function': function,
            'code_context': code_context,
            'locals': locals_dict,
            'args': args,
            'module': module,
        }

    def _get_code_context(
        self,
        filename: str,
        lineno: int,
        context: int = 2
    ) -> list[str] | None:
        """Get lines of code around the given line number."""
        try:
            lines = []
            for i in range(lineno - context, lineno + context + 1):
                if i > 0:
                    line = linecache.getline(filename, i)
                    if line:
                        lines.append(line)
                    elif i <= lineno:
                        # Only pad before current line
                        lines.append('')
            return lines if lines else None
        except Exception:
            return None

    def _short_path(self, filepath: str) -> str:
        """Shorten a file path for display."""
        # Try to make relative to cwd
        try:
            cwd = os.getcwd()
            if filepath.startswith(cwd):
                return filepath[len(cwd):].lstrip(os.sep)
        except Exception:
            pass

        # Try to shorten site-packages paths
        if 'site-packages' in filepath:
            parts = filepath.split('site-packages')
            if len(parts) > 1:
                return '...' + parts[1]

        return filepath

    def _analyze_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        frames: list[FrameInfo]
    ) -> str | None:
        """Generate analysis/hints about the exception."""
        hints = []

        exc_name = exc_type.__name__
        exc_msg = str(exc_value)

        # Get crash frame info
        crash_frame = frames[-1] if frames else None

        # KeyError analysis
        if exc_name == 'KeyError' and crash_frame:
            key = exc_msg.strip("'\"")
            # Try to find the dict that was accessed
            for name, value in crash_frame.locals.items():
                if isinstance(value, dict):
                    if key not in value:
                        available = list(value.keys())[:5]
                        hints.append(f"Problem: Key '{key}' not found in '{name}'")
                        hints.append(f"Available keys: {available}")
                        break

        # AttributeError analysis
        elif exc_name == 'AttributeError' and crash_frame:
            # Parse "object has no attribute 'x'"
            if "has no attribute" in exc_msg:
                attr = exc_msg.split("'")[1] if "'" in exc_msg else "?"
                hints.append(f"Problem: Attribute '{attr}' does not exist")
                # Try to find the object
                for name, value in crash_frame.locals.items():
                    if hasattr(value, '__dict__'):
                        available = [k for k in dir(value) if not k.startswith('_')][:5]
                        hints.append(f"'{name}' has: {available}...")
                        break

        # TypeError for wrong arguments
        elif exc_name == 'TypeError' and 'argument' in exc_msg:
            hints.append(f"Problem: {exc_msg}")
            if crash_frame and crash_frame.args:
                hints.append(f"Received arguments: {list(crash_frame.args.keys())}")

        # ValueError analysis
        elif exc_name == 'ValueError':
            hints.append(f"Problem: {exc_msg}")
            if crash_frame:
                # Show local values that might be relevant
                for name, value in crash_frame.locals.items():
                    if not name.startswith('_'):
                        hints.append(f"  {name} = {repr(value)[:50]}")

        # IndexError analysis
        elif exc_name == 'IndexError' and crash_frame:
            hints.append(f"Problem: {exc_msg}")
            for name, value in crash_frame.locals.items():
                if isinstance(value, (list, tuple)):
                    hints.append(f"  {name} has {len(value)} items (indices 0-{len(value)-1})")

        # ImportError analysis
        elif exc_name in ('ImportError', 'ModuleNotFoundError'):
            hints.append(f"Problem: {exc_msg}")
            hints.append("Check: Is the package installed? Is the path correct?")

        if hints:
            return '\n'.join(hints)
        return None


def install_crash_handler(
    focus: list[str] | None = None,
    collapse: list[str] | None = None,
    show_stdlib: bool = False,
    **kwargs
) -> CrashHandler:
    """
    Install the crash handler as the global exception handler.

    Args:
        focus: Only show frames from these packages
        collapse: Collapse frames from these packages
        show_stdlib: Whether to show stdlib frames
        **kwargs: Additional arguments for CrashHandler

    Returns:
        The installed CrashHandler instance
    """
    handler = CrashHandler(
        focus=focus,
        collapse=collapse,
        show_stdlib=show_stdlib,
        **kwargs
    )
    handler.install()
    return handler
