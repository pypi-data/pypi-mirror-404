"""
Formatter for clean, LLM-readable output.

Produces well-structured text with clear visual hierarchy:
- Double lines for major sections
- Single lines for subsections
- Consistent indentation
- Code context with line numbers
- Instrumentation data (breadcrumbs, resources, memory, timing)
"""

from dataclasses import dataclass
from typing import Any
import textwrap

from .collector import (
    Breadcrumb,
    BreadcrumbType,
    ResourceSnapshot,
    MemoryAllocation,
    TimingRecord,
)


# Box drawing characters for clean output
DOUBLE_LINE = "═" * 70
SINGLE_LINE = "─" * 70
ARROW = "→"
MARKER = ">>"


@dataclass
class FrameInfo:
    """Information about a single stack frame."""
    filename: str
    lineno: int
    function: str
    code_context: list[str] | None
    locals: dict[str, Any]
    args: dict[str, Any] | None = None
    is_crash_site: bool = False


class Formatter:
    """Formats debugging output for LLM consumption."""

    def __init__(self, max_value_length: int = 200, context_lines: int = 2):
        self.max_value_length = max_value_length
        self.context_lines = context_lines

    def format_crash(
        self,
        exc_type: type,
        exc_value: BaseException,
        frames: list[FrameInfo],
        call_chain: list[str],
        collapsed: dict[str, int] | None = None,
        analysis: str | None = None,
        breadcrumbs: list[Breadcrumb] | None = None,
        resource_snapshot: ResourceSnapshot | None = None,
        memory_allocations: list[MemoryAllocation] | None = None,
        timing_records: list[TimingRecord] | None = None,
    ) -> str:
        """Format a crash report with full instrumentation data."""
        lines = []

        # Header
        lines.append(DOUBLE_LINE)
        lines.append(f"CRASH: {exc_type.__name__}")
        lines.append(DOUBLE_LINE)
        lines.append("")
        lines.append(f"Message: {exc_value}")

        # Find crash location
        crash_frame = next((f for f in frames if f.is_crash_site), frames[-1] if frames else None)
        if crash_frame:
            lines.append(f"Location: {crash_frame.filename}:{crash_frame.lineno} in {crash_frame.function}()")

        lines.append("")

        # Call chain
        lines.append(SINGLE_LINE)
        lines.append("CALL CHAIN")
        lines.append(SINGLE_LINE)
        lines.append("")
        lines.append(f"    {' → '.join(call_chain)}")
        lines.append("")

        # Show collapsed frames info
        if collapsed:
            for package, count in collapsed.items():
                lines.append(f"    [{package}: {count} frames hidden]")
            lines.append("")

        # Each relevant frame
        for i, frame in enumerate(frames, 1):
            lines.append(SINGLE_LINE)
            crash_marker = "  ← CRASH HERE" if frame.is_crash_site else ""
            lines.append(f"FRAME {i}: {frame.filename}:{frame.lineno}{crash_marker}")
            lines.append(SINGLE_LINE)
            lines.append("")

            # Function signature
            if frame.args:
                args_str = ", ".join(frame.args.keys())
                lines.append(f"Function: {frame.function}({args_str})")
            else:
                lines.append(f"Function: {frame.function}()")
            lines.append("")

            # Code context
            if frame.code_context:
                lines.extend(self._format_code_context(
                    frame.code_context,
                    frame.lineno,
                    self.context_lines
                ))
                lines.append("")

            # Arguments (if available and different from locals)
            if frame.args:
                lines.append("Arguments:")
                for name, value in frame.args.items():
                    lines.append(f"    {name:12} = {self._format_value(value)}")
                lines.append("")

            # Locals
            display_locals = {k: v for k, v in frame.locals.items()
                           if not k.startswith('_') and k not in (frame.args or {})}
            if display_locals:
                lines.append("Locals:")
                for name, value in display_locals.items():
                    lines.append(f"    {name:12} = {self._format_value(value)}")
                lines.append("")
            elif not frame.args:
                lines.append("Locals:")
                lines.append("    (none)")
                lines.append("")

        # I/O Trail (breadcrumbs)
        if breadcrumbs:
            lines.extend(self._format_breadcrumbs(breadcrumbs))

        # Resource State
        if resource_snapshot:
            lines.extend(self._format_resource_snapshot(resource_snapshot))

        # Memory Allocations
        if memory_allocations:
            lines.extend(self._format_memory_allocations(memory_allocations))

        # Timing / Slow Operations
        if timing_records:
            slow = [r for r in timing_records if r.is_slow]
            if slow:
                lines.extend(self._format_timing_records(slow, title="SLOW OPERATIONS"))

        # Analysis section
        if analysis:
            lines.append(SINGLE_LINE)
            lines.append("ANALYSIS")
            lines.append(SINGLE_LINE)
            lines.append("")
            for line in analysis.split('\n'):
                lines.append(line)
            lines.append("")

        lines.append(DOUBLE_LINE)

        return '\n'.join(lines)

    def _format_breadcrumbs(self, breadcrumbs: list[Breadcrumb]) -> list[str]:
        """Format the I/O breadcrumb trail."""
        lines = []
        lines.append(SINGLE_LINE)
        lines.append("I/O TRAIL (recent activity)")
        lines.append(SINGLE_LINE)
        lines.append("")

        # Group by type for cleaner output
        by_type: dict[BreadcrumbType, list[Breadcrumb]] = {}
        for b in breadcrumbs:
            by_type.setdefault(b.type, []).append(b)

        # Show most relevant types first
        type_order = [
            BreadcrumbType.HTTP,
            BreadcrumbType.DB,
            BreadcrumbType.FILE,
            BreadcrumbType.SOCKET,
            BreadcrumbType.SUBPROCESS,
            BreadcrumbType.CONFIG,
            BreadcrumbType.IMPORT,
        ]

        for btype in type_order:
            if btype not in by_type:
                continue
            items = by_type[btype]

            lines.append(f"  [{btype.value}]")
            for b in items[-10:]:  # Last 10 of each type
                duration_str = ""
                if b.duration is not None:
                    if b.duration < 0.001:
                        duration_str = f" ({b.duration*1000000:.0f}μs)"
                    elif b.duration < 1:
                        duration_str = f" ({b.duration*1000:.1f}ms)"
                    else:
                        duration_str = f" ({b.duration:.2f}s)"

                lines.append(f"    • {b.message}{duration_str}")

                # Show key data fields
                if b.data:
                    important_keys = ['error', 'status_code', 'query_type', 'table', 'host', 'port']
                    extras = []
                    for key in important_keys:
                        if key in b.data:
                            extras.append(f"{key}={b.data[key]}")
                    if extras:
                        lines.append(f"      {', '.join(extras)}")

            lines.append("")

        # Show custom breadcrumbs last
        if BreadcrumbType.CUSTOM in by_type:
            lines.append("  [CUSTOM]")
            for b in by_type[BreadcrumbType.CUSTOM][-5:]:
                lines.append(f"    • {b.message}")
            lines.append("")

        return lines

    def _format_resource_snapshot(self, snapshot: ResourceSnapshot) -> list[str]:
        """Format the resource state snapshot."""
        lines = []
        lines.append(SINGLE_LINE)
        lines.append("RESOURCE STATE (at crash)")
        lines.append(SINGLE_LINE)
        lines.append("")

        # Memory
        if snapshot.memory_rss is not None:
            lines.append("  Memory:")
            lines.append(f"    RSS:     {self._format_bytes(snapshot.memory_rss)}")
            if snapshot.memory_vms is not None:
                lines.append(f"    VMS:     {self._format_bytes(snapshot.memory_vms)}")
            if snapshot.memory_percent is not None:
                lines.append(f"    Percent: {snapshot.memory_percent:.1f}%")
            lines.append("")

        # CPU
        if snapshot.cpu_percent is not None:
            lines.append(f"  CPU: {snapshot.cpu_percent:.1f}%")
            lines.append("")

        # Threads
        if snapshot.thread_count is not None:
            lines.append(f"  Threads: {snapshot.thread_count}")
            lines.append("")

        # Open files (if any)
        if snapshot.open_files:
            lines.append(f"  Open Files ({len(snapshot.open_files)}):")
            for f in snapshot.open_files[:10]:
                # Shorten long paths
                if len(f) > 60:
                    f = "..." + f[-57:]
                lines.append(f"    • {f}")
            if len(snapshot.open_files) > 10:
                lines.append(f"    ... and {len(snapshot.open_files) - 10} more")
            lines.append("")

        # Network connections (if any)
        if snapshot.connections:
            lines.append(f"  Network Connections ({len(snapshot.connections)}):")
            for conn in snapshot.connections[:5]:
                status = conn.get('status', '?')
                local = conn.get('local', '?')
                remote = conn.get('remote', '')
                if remote:
                    lines.append(f"    • {local} → {remote} ({status})")
                else:
                    lines.append(f"    • {local} ({status})")
            if len(snapshot.connections) > 5:
                lines.append(f"    ... and {len(snapshot.connections) - 5} more")
            lines.append("")

        return lines

    def _format_memory_allocations(self, allocations: list[MemoryAllocation]) -> list[str]:
        """Format top memory allocations."""
        lines = []
        lines.append(SINGLE_LINE)
        lines.append("TOP MEMORY ALLOCATIONS")
        lines.append(SINGLE_LINE)
        lines.append("")

        for alloc in allocations[:10]:
            # Shorten filename
            filename = alloc.filename
            if len(filename) > 40:
                filename = "..." + filename[-37:]

            size_str = self._format_bytes(alloc.size)
            lines.append(f"  {size_str:>10}  {filename}:{alloc.lineno}  ({alloc.count} allocs)")

        lines.append("")
        return lines

    def _format_timing_records(self, records: list[TimingRecord], title: str = "TIMING") -> list[str]:
        """Format timing records."""
        lines = []
        lines.append(SINGLE_LINE)
        lines.append(title)
        lines.append(SINGLE_LINE)
        lines.append("")

        # Sort by duration (slowest first)
        sorted_records = sorted(records, key=lambda r: r.duration_ms, reverse=True)

        for record in sorted_records[:10]:
            duration_str = self._format_duration(record.duration_ms)
            slow_marker = " ⚠ SLOW" if record.is_slow else ""
            lines.append(f"  {duration_str:>10}  {record.name} [{record.category}]{slow_marker}")

        lines.append("")
        return lines

    def _format_bytes(self, size: int) -> str:
        """Format bytes as human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(size) < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def _format_duration(self, ms: float) -> str:
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

    def format_trace(
        self,
        calls: list[dict],
        summary: dict | None = None,
    ) -> str:
        """Format an execution trace."""
        lines = []

        lines.append(DOUBLE_LINE)
        lines.append("EXECUTION TRACE")
        lines.append(DOUBLE_LINE)
        lines.append("")

        # Build tree structure
        lines.extend(self._format_call_tree(calls))

        # Summary
        if summary:
            lines.append("")
            lines.append(SINGLE_LINE)
            lines.append("SUMMARY")
            lines.append(SINGLE_LINE)
            lines.append("")
            for key, value in summary.items():
                lines.append(f"{key:12}: {value}")

        lines.append("")
        lines.append(DOUBLE_LINE)

        return '\n'.join(lines)

    def format_hang(
        self,
        frame: FrameInfo,
        duration: float,
        loop_info: dict | None = None,
        likely_issue: str | None = None,
        breadcrumbs: list[Breadcrumb] | None = None,
        resource_snapshot: ResourceSnapshot | None = None,
    ) -> str:
        """Format output for an interrupted/hanging process."""
        lines = []

        lines.append(DOUBLE_LINE)
        lines.append(f"INTERRUPTED (after {duration:.1f}s)")
        lines.append(DOUBLE_LINE)
        lines.append("")
        lines.append(f"Stuck at: {frame.filename}:{frame.lineno} in {frame.function}()")
        lines.append("")

        lines.append(SINGLE_LINE)
        lines.append("CURRENT STATE")
        lines.append(SINGLE_LINE)
        lines.append("")

        # Code context
        if frame.code_context:
            lines.extend(self._format_code_context(
                frame.code_context,
                frame.lineno,
                self.context_lines
            ))
            lines.append("")

        # Loop info if available
        if loop_info:
            lines.append("Loop Progress:")
            for key, value in loop_info.items():
                lines.append(f"    {key:12}: {value}")
            lines.append("")

        # Locals
        if frame.locals:
            lines.append("Locals:")
            for name, value in frame.locals.items():
                if not name.startswith('_'):
                    lines.append(f"    {name:12} = {self._format_value(value)}")
            lines.append("")

        # I/O Trail
        if breadcrumbs:
            lines.extend(self._format_breadcrumbs(breadcrumbs))

        # Resource State
        if resource_snapshot:
            lines.extend(self._format_resource_snapshot(resource_snapshot))

        # Likely issue
        if likely_issue:
            lines.append(SINGLE_LINE)
            lines.append("LIKELY ISSUE")
            lines.append(SINGLE_LINE)
            lines.append("")
            lines.append(likely_issue)
            lines.append("")

        lines.append(DOUBLE_LINE)

        return '\n'.join(lines)

    def _format_code_context(
        self,
        code_lines: list[str],
        current_lineno: int,
        context: int
    ) -> list[str]:
        """Format code with line numbers and current line marker."""
        lines = []

        # Calculate starting line number
        start_lineno = current_lineno - context

        for i, code in enumerate(code_lines):
            lineno = start_lineno + i
            code = code.rstrip()

            if lineno == current_lineno:
                lines.append(f"{MARKER} {lineno:4}│ {code}")
            else:
                lines.append(f"   {lineno:4}│ {code}")

        return lines

    def _format_value(self, value: Any) -> str:
        """Format a value for display, truncating if needed."""
        try:
            # Try to get a meaningful representation
            if hasattr(value, '__class__'):
                type_name = type(value).__name__

                # Special handling for common types
                if isinstance(value, str):
                    repr_str = repr(value)
                elif isinstance(value, (list, tuple)):
                    if len(value) > 5:
                        repr_str = f"{type_name}([{len(value)} items])"
                    else:
                        repr_str = repr(value)
                elif isinstance(value, dict):
                    if len(value) > 5:
                        keys = list(value.keys())[:3]
                        repr_str = f"dict({len(value)} items, keys: {keys}...)"
                    else:
                        repr_str = repr(value)
                elif hasattr(value, '__dict__'):
                    # Object with attributes
                    attrs = {k: v for k, v in value.__dict__.items()
                            if not k.startswith('_')}
                    if attrs:
                        attr_str = ', '.join(f'{k}={self._short_repr(v)}'
                                           for k, v in list(attrs.items())[:3])
                        repr_str = f"{type_name}({attr_str})"
                    else:
                        repr_str = f"<{type_name}>"
                else:
                    repr_str = repr(value)
            else:
                repr_str = repr(value)

            # Truncate if too long
            if len(repr_str) > self.max_value_length:
                repr_str = repr_str[:self.max_value_length - 3] + "..."

            return repr_str

        except Exception:
            return f"<error formatting {type(value).__name__}>"

    def _short_repr(self, value: Any) -> str:
        """Get a very short representation of a value."""
        try:
            r = repr(value)
            if len(r) > 20:
                return r[:17] + "..."
            return r
        except Exception:
            return "?"

    def _format_call_tree(self, calls: list[dict], indent: int = 0) -> list[str]:
        """Format calls as a tree structure."""
        lines = []
        prefix = "│   " * indent

        for i, call in enumerate(calls):
            is_last = i == len(calls) - 1
            branch = "└─" if is_last else "├─"

            # Function call
            func = call.get('function', '?')
            args = call.get('args', '')
            lines.append(f"{prefix}{branch}→ {func}({args})")

            # Return value if present
            if 'returned' in call:
                ret_prefix = "    " if is_last else "│   "
                lines.append(f"{prefix}{ret_prefix}  returned {call['returned']}")

            # Nested calls
            if 'calls' in call:
                child_prefix = "    " if is_last else "│   "
                for child_line in self._format_call_tree(call['calls'], indent + 1):
                    lines.append(child_line)

        return lines
