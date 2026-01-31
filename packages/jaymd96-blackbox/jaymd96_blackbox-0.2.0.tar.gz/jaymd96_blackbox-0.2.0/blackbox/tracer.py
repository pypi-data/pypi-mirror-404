"""
Execution tracer for following code execution flow.

Records function calls, returns, and variable changes,
then outputs a clean trace for LLM consumption.
"""

import sys
import os
import time
import threading
from dataclasses import dataclass, field
from types import FrameType
from typing import Any, Callable

from .formatter import Formatter
from .filters import Filter


@dataclass
class CallRecord:
    """Record of a single function call."""
    function: str
    filename: str
    lineno: int
    args: dict[str, Any]
    start_time: float
    end_time: float | None = None
    return_value: Any = None
    exception: BaseException | None = None
    children: list['CallRecord'] = field(default_factory=list)


class Tracer:
    """
    Traces execution and records function calls/returns.

    Usage:
        tracer = Tracer(focus=['mypackage'])
        with tracer:
            my_function()
        print(tracer.format())
    """

    def __init__(
        self,
        focus: list[str] | None = None,
        max_depth: int | None = None,
        trace_returns: bool = True,
        trace_args: bool = True,
        max_call_records: int = 1000,
    ):
        self.filter = Filter(focus=focus or [])
        self.max_depth = max_depth
        self.trace_returns = trace_returns
        self.trace_args = trace_args
        self.max_call_records = max_call_records

        self.formatter = Formatter()

        self._root_calls: list[CallRecord] = []
        self._call_stack: list[CallRecord] = []
        self._record_count = 0
        self._start_time: float = 0
        self._end_time: float = 0
        self._truncated = False

        self._lock = threading.Lock()
        self._original_trace: Callable | None = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

    def start(self):
        """Start tracing."""
        self._start_time = time.time()
        self._root_calls = []
        self._call_stack = []
        self._record_count = 0
        self._truncated = False

        self._original_trace = sys.gettrace()
        sys.settrace(self._trace_callback)

    def stop(self):
        """Stop tracing."""
        sys.settrace(self._original_trace)
        self._end_time = time.time()

    def format(self) -> str:
        """Format the trace output."""
        calls = self._records_to_dicts(self._root_calls)

        summary = {
            'Duration': f'{self._end_time - self._start_time:.3f}s',
            'Calls': self._record_count,
            'Max depth': self._get_max_depth(self._root_calls),
        }

        if self._truncated:
            summary['Note'] = f'Truncated at {self.max_call_records} calls'

        return self.formatter.format_trace(calls, summary)

    def _trace_callback(
        self,
        frame: FrameType,
        event: str,
        arg: Any
    ) -> Callable | None:
        """Trace function called by Python for each event."""
        # Check if we've exceeded max records
        if self._record_count >= self.max_call_records:
            self._truncated = True
            return None

        # Get frame info
        filename = frame.f_code.co_filename
        function = frame.f_code.co_name
        module = frame.f_globals.get('__name__', '')

        # Filter out unwanted frames
        if not self._should_trace(filename, module):
            return None

        # Check depth limit
        if self.max_depth and len(self._call_stack) >= self.max_depth:
            return self._trace_callback

        with self._lock:
            if event == 'call':
                self._handle_call(frame, function, filename)
            elif event == 'return':
                self._handle_return(arg)
            elif event == 'exception':
                self._handle_exception(arg)

        return self._trace_callback

    def _should_trace(self, filename: str, module: str) -> bool:
        """Check if this frame should be traced."""
        # Skip internal frames
        if filename.startswith('<'):
            return False

        # Skip blackbox itself
        if 'blackbox' in filename:
            return False

        # Apply focus filter
        if self.filter.focus:
            return self.filter._matches_any(filename, module, self.filter.focus)

        # Skip stdlib if no focus specified
        if self.filter._is_stdlib(filename):
            return False

        return True

    def _handle_call(self, frame: FrameType, function: str, filename: str):
        """Handle a function call event."""
        # Extract arguments
        args = {}
        if self.trace_args:
            try:
                code = frame.f_code
                arg_count = code.co_argcount + code.co_kwonlyargcount
                arg_names = code.co_varnames[:arg_count]

                for name in arg_names:
                    if name in frame.f_locals:
                        value = frame.f_locals[name]
                        args[name] = self._safe_repr(value)
            except Exception:
                pass

        record = CallRecord(
            function=function,
            filename=self._short_path(filename),
            lineno=frame.f_lineno,
            args=args,
            start_time=time.time(),
        )

        # Add to tree
        if self._call_stack:
            self._call_stack[-1].children.append(record)
        else:
            self._root_calls.append(record)

        self._call_stack.append(record)
        self._record_count += 1

    def _handle_return(self, return_value: Any):
        """Handle a function return event."""
        if not self._call_stack:
            return

        record = self._call_stack.pop()
        record.end_time = time.time()

        if self.trace_returns:
            record.return_value = self._safe_repr(return_value)

    def _handle_exception(self, exc_info: tuple):
        """Handle an exception event."""
        if not self._call_stack:
            return

        exc_type, exc_value, _ = exc_info
        self._call_stack[-1].exception = exc_value

    def _safe_repr(self, value: Any, max_len: int = 50) -> str:
        """Get a safe string representation of a value."""
        try:
            r = repr(value)
            if len(r) > max_len:
                r = r[:max_len - 3] + '...'
            return r
        except Exception:
            return f'<{type(value).__name__}>'

    def _short_path(self, filepath: str) -> str:
        """Shorten a file path for display."""
        try:
            cwd = os.getcwd()
            if filepath.startswith(cwd):
                return filepath[len(cwd):].lstrip(os.sep)
        except Exception:
            pass
        return filepath

    def _records_to_dicts(self, records: list[CallRecord]) -> list[dict]:
        """Convert call records to dictionaries for formatting."""
        result = []

        for record in records:
            d = {
                'function': record.function,
                'file': record.filename,
                'line': record.lineno,
            }

            if record.args:
                args_str = ', '.join(f'{k}={v}' for k, v in record.args.items())
                d['args'] = args_str

            if record.return_value is not None:
                d['returned'] = record.return_value

            if record.exception:
                d['exception'] = str(record.exception)

            if record.children:
                d['calls'] = self._records_to_dicts(record.children)

            result.append(d)

        return result

    def _get_max_depth(self, records: list[CallRecord], depth: int = 1) -> int:
        """Get the maximum depth of the call tree."""
        if not records:
            return depth - 1

        max_child_depth = depth
        for record in records:
            if record.children:
                child_depth = self._get_max_depth(record.children, depth + 1)
                max_child_depth = max(max_child_depth, child_depth)

        return max_child_depth


def trace_execution(
    focus: list[str] | None = None,
    max_depth: int | None = None,
) -> Tracer:
    """
    Create a tracer for following code execution.

    Usage:
        with trace_execution(focus=['mypackage']) as tracer:
            my_function()
        print(tracer.format())

    Args:
        focus: Only trace functions from these packages
        max_depth: Maximum call depth to trace

    Returns:
        A Tracer context manager
    """
    return Tracer(focus=focus, max_depth=max_depth)
