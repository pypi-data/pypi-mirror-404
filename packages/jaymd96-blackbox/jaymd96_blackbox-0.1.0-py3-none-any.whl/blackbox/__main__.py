"""
Entry point for python -m blackbox.

Usage:
    python -m blackbox script.py [args...]
    python -m blackbox --trace script.py
    python -m blackbox --focus mypackage script.py
"""

import sys
import os
import argparse
import runpy
import signal
import time

from .crash import CrashHandler
from .tracer import Tracer
from .formatter import Formatter, FrameInfo
from .instruments import install_all_hooks, uninstall_all_hooks
from .collector import get_collector


def main():
    parser = argparse.ArgumentParser(
        prog='python -m blackbox',
        description='LLM-friendly Python debugger with structured output',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m blackbox script.py              Run with crash handling
  python -m blackbox --trace script.py      Run with execution tracing
  python -m blackbox --focus mypackage script.py
                                            Only show mypackage frames
  python -m blackbox --timeout 30 script.py Interrupt after 30 seconds
""",
    )

    parser.add_argument(
        'script',
        help='Python script to run',
    )
    parser.add_argument(
        'args',
        nargs='*',
        help='Arguments to pass to the script',
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--trace',
        action='store_true',
        help='Enable execution tracing (shows all function calls)',
    )
    mode_group.add_argument(
        '--crash-only',
        action='store_true',
        default=True,
        help='Only output on crash (default)',
    )

    # Filtering options
    parser.add_argument(
        '--focus',
        action='append',
        dest='focus',
        metavar='PACKAGE',
        help='Only show frames from these packages (can be repeated)',
    )
    parser.add_argument(
        '--collapse',
        action='append',
        dest='collapse',
        metavar='PACKAGE',
        help='Collapse frames from these packages (can be repeated)',
    )
    parser.add_argument(
        '--show-stdlib',
        action='store_true',
        help='Show standard library frames (hidden by default)',
    )
    parser.add_argument(
        '--max-depth',
        type=int,
        metavar='N',
        help='Maximum number of frames to show',
    )

    # Output options
    parser.add_argument(
        '--context',
        type=int,
        default=2,
        metavar='N',
        help='Lines of code context around crash (default: 2)',
    )
    parser.add_argument(
        '--max-value-length',
        type=int,
        default=200,
        metavar='N',
        help='Maximum length for value representations (default: 200)',
    )

    # Timeout/hang detection
    parser.add_argument(
        '--timeout',
        type=float,
        metavar='SECONDS',
        help='Interrupt and report after N seconds',
    )

    # Output destination
    parser.add_argument(
        '-o', '--output',
        type=str,
        metavar='FILE',
        help='Write output to file instead of stderr',
    )

    # Instrumentation control
    parser.add_argument(
        '--no-instrumentation',
        action='store_true',
        help='Disable all instrumentation (just crash handling)',
    )
    parser.add_argument(
        '--slow-threshold',
        type=float,
        default=100.0,
        metavar='MS',
        help='Threshold in ms for marking operations as slow (default: 100)',
    )

    args = parser.parse_args()

    # Validate script exists
    if not os.path.exists(args.script):
        print(f"Error: Script not found: {args.script}", file=sys.stderr)
        sys.exit(1)

    # Set up output
    output_file = sys.stderr
    if args.output:
        output_file = open(args.output, 'w')

    # Set up sys.argv for the script
    sys.argv = [args.script] + args.args

    # Add script directory to path
    script_dir = os.path.dirname(os.path.abspath(args.script))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    if args.trace:
        # Trace mode
        run_with_trace(
            args.script,
            focus=args.focus,
            max_depth=args.max_depth,
            timeout=args.timeout,
            output_file=output_file,
        )
    else:
        # Crash-only mode (default)
        run_with_crash_handler(
            args.script,
            focus=args.focus,
            collapse=args.collapse,
            show_stdlib=args.show_stdlib,
            max_depth=args.max_depth,
            context_lines=args.context,
            max_value_length=args.max_value_length,
            timeout=args.timeout,
            output_file=output_file,
            enable_instrumentation=not args.no_instrumentation,
            slow_threshold_ms=args.slow_threshold,
        )


def run_with_crash_handler(
    script: str,
    focus: list[str] | None,
    collapse: list[str] | None,
    show_stdlib: bool,
    max_depth: int | None,
    context_lines: int,
    max_value_length: int,
    timeout: float | None,
    output_file,
    enable_instrumentation: bool = True,
    slow_threshold_ms: float = 100.0,
):
    """Run script with crash handler and full instrumentation."""
    # Install all instrumentation hooks
    if enable_instrumentation:
        from .instruments.timing import set_slow_threshold
        set_slow_threshold(slow_threshold_ms)
        hook_results = install_all_hooks()
    else:
        hook_results = {}

    handler = CrashHandler(
        focus=focus,
        collapse=collapse,
        show_stdlib=show_stdlib,
        max_depth=max_depth,
        context_lines=context_lines,
        max_value_length=max_value_length,
        output_file=output_file,
    )
    handler.install()

    # Set up timeout if specified
    start_time = time.time()
    if timeout:
        def timeout_handler(signum, frame):
            elapsed = time.time() - start_time
            output = format_hang(frame, elapsed, handler.formatter)
            print(output, file=output_file)
            output_file.flush()
            os._exit(124)  # Use _exit to avoid triggering exception handlers

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.setitimer(signal.ITIMER_REAL, timeout)

    try:
        # Run the script
        runpy.run_path(script, run_name='__main__')
    except SystemExit:
        raise
    except BaseException as e:
        # Manually format and print the exception
        # (sys.excepthook doesn't trigger for exceptions in runpy)
        output = handler.format_exception(type(e), e, e.__traceback__)
        print(output, file=output_file)
        sys.exit(1)
    finally:
        if timeout:
            signal.setitimer(signal.ITIMER_REAL, 0)
        handler.uninstall()
        if enable_instrumentation:
            uninstall_all_hooks()


def run_with_trace(
    script: str,
    focus: list[str] | None,
    max_depth: int | None,
    timeout: float | None,
    output_file,
):
    """Run script with execution tracing."""
    tracer = Tracer(
        focus=focus,
        max_depth=max_depth,
    )

    # Set up timeout if specified
    start_time = time.time()
    if timeout:
        def timeout_handler(signum, frame):
            tracer.stop()
            print(tracer.format(), file=output_file)
            elapsed = time.time() - start_time
            print(f"\n[Interrupted after {elapsed:.1f}s]", file=output_file)
            sys.exit(124)

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.setitimer(signal.ITIMER_REAL, timeout)

    try:
        with tracer:
            runpy.run_path(script, run_name='__main__')
    finally:
        if timeout:
            signal.setitimer(signal.ITIMER_REAL, 0)

    # Print trace output
    print(tracer.format(), file=output_file)


def format_hang(frame, duration: float, formatter: Formatter) -> str:
    """Format output when script is interrupted due to timeout."""
    import linecache
    import inspect
    from .instruments.resources import capture_resource_snapshot

    # Get code context
    filename = frame.f_code.co_filename
    lineno = frame.f_lineno
    function = frame.f_code.co_name

    code_context = []
    for i in range(lineno - 2, lineno + 3):
        if i > 0:
            line = linecache.getline(filename, i)
            if line:
                code_context.append(line)

    # Get locals
    locals_dict = {}
    for name, value in frame.f_locals.items():
        if not name.startswith('_') and not inspect.ismodule(value):
            locals_dict[name] = value

    # Shorten path
    try:
        cwd = os.getcwd()
        if filename.startswith(cwd):
            filename = filename[len(cwd):].lstrip(os.sep)
    except Exception:
        pass

    frame_info = FrameInfo(
        filename=filename,
        lineno=lineno,
        function=function,
        code_context=code_context,
        locals=locals_dict,
    )

    # Try to detect loop info
    loop_info = None
    for name, value in locals_dict.items():
        if isinstance(value, int) and name in ('i', 'j', 'idx', 'index', 'count', 'n'):
            loop_info = {'Current index': f'{name} = {value}'}
            break

    # Gather instrumentation data
    collector = get_collector()
    breadcrumbs = collector.get_breadcrumbs()
    resource_snapshot = capture_resource_snapshot()

    return formatter.format_hang(
        frame=frame_info,
        duration=duration,
        loop_info=loop_info,
        likely_issue="Script timed out - may be stuck in a loop or waiting for I/O",
        breadcrumbs=breadcrumbs if breadcrumbs else None,
        resource_snapshot=resource_snapshot,
    )


if __name__ == '__main__':
    main()
