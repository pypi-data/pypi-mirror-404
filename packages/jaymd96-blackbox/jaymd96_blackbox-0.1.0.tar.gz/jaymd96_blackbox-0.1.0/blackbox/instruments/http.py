"""
HTTP instrumentation using wrapt.

Captures:
- requests library calls (get, post, put, delete, etc.)
- httpx library calls
- urllib3 connections
"""

import time
from typing import Any, Callable

from ..collector import get_collector, BreadcrumbType


# Track if wrapt is available and hooks installed
_wrapt_available = False
try:
    import wrapt
    _wrapt_available = True
except ImportError:
    wrapt = None

_hooks_installed = False
_original_functions: dict[str, Callable] = {}


def is_wrapt_available() -> bool:
    """Check if wrapt is available."""
    return _wrapt_available


def _create_request_wrapper(method: str) -> Callable:
    """Create a wrapper function for HTTP methods."""

    def wrapper(wrapped: Callable, instance: Any, args: tuple, kwargs: dict) -> Any:
        url = args[0] if args else kwargs.get('url', '?')
        start_time = time.time()

        try:
            response = wrapped(*args, **kwargs)
            duration = time.time() - start_time

            # Extract response info
            status_code = getattr(response, 'status_code', '?')
            content_length = None
            if hasattr(response, 'headers'):
                content_length = response.headers.get('content-length')

            # Create breadcrumb
            message = f"{method.upper()} {_truncate_url(url)} → {status_code}"
            data = {
                "method": method.upper(),
                "url": str(url),
                "status_code": status_code,
            }
            if content_length:
                data["content_length"] = content_length

            get_collector().add_breadcrumb(
                type=BreadcrumbType.HTTP,
                category="request",
                message=message,
                data=data,
                duration=duration,
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Log failed request
            message = f"{method.upper()} {_truncate_url(url)} → FAILED: {type(e).__name__}"
            data = {
                "method": method.upper(),
                "url": str(url),
                "error": str(e),
                "error_type": type(e).__name__,
            }

            get_collector().add_breadcrumb(
                type=BreadcrumbType.HTTP,
                category="request",
                message=message,
                data=data,
                duration=duration,
            )

            raise

    return wrapper


def _truncate_url(url: str, max_length: int = 60) -> str:
    """Truncate URL for display."""
    url_str = str(url)
    if len(url_str) <= max_length:
        return url_str

    # Try to keep the important parts
    # Remove query string if too long
    if '?' in url_str:
        base, query = url_str.split('?', 1)
        if len(base) <= max_length - 5:
            return base + "?..."
        return base[:max_length - 3] + "..."

    return url_str[:max_length - 3] + "..."


def install_http_hooks() -> bool:
    """
    Install HTTP instrumentation hooks.

    Returns True if hooks installed, False if wrapt not available.
    """
    global _hooks_installed

    if not _wrapt_available:
        return False

    if _hooks_installed:
        return True

    # Try to wrap requests library
    try:
        import requests

        for method in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
            wrapt.wrap_function_wrapper(
                'requests',
                method,
                _create_request_wrapper(method)
            )

        # Also wrap Session methods
        for method in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'request']:
            wrapt.wrap_function_wrapper(
                'requests',
                f'Session.{method}',
                _create_request_wrapper(method)
            )

    except ImportError:
        pass  # requests not installed

    # Try to wrap httpx library
    try:
        import httpx

        for method in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
            wrapt.wrap_function_wrapper(
                'httpx',
                method,
                _create_request_wrapper(method)
            )

        # Client methods
        for method in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'request']:
            wrapt.wrap_function_wrapper(
                'httpx',
                f'Client.{method}',
                _create_request_wrapper(method)
            )

    except ImportError:
        pass  # httpx not installed

    # Try to wrap urllib3
    try:
        import urllib3

        def urllib3_wrapper(wrapped: Callable, instance: Any, args: tuple, kwargs: dict) -> Any:
            method = kwargs.get('method', args[0] if args else 'GET')
            url = kwargs.get('url', args[1] if len(args) > 1 else '?')
            start_time = time.time()

            try:
                response = wrapped(*args, **kwargs)
                duration = time.time() - start_time

                message = f"{method} {_truncate_url(url)} → {response.status}"
                get_collector().add_breadcrumb(
                    type=BreadcrumbType.HTTP,
                    category="urllib3",
                    message=message,
                    data={"method": method, "url": str(url), "status": response.status},
                    duration=duration,
                )

                return response
            except Exception as e:
                duration = time.time() - start_time

                message = f"{method} {_truncate_url(url)} → FAILED"
                get_collector().add_breadcrumb(
                    type=BreadcrumbType.HTTP,
                    category="urllib3",
                    message=message,
                    data={"method": method, "url": str(url), "error": str(e)},
                    duration=duration,
                )
                raise

        wrapt.wrap_function_wrapper(
            'urllib3',
            'HTTPConnectionPool.urlopen',
            urllib3_wrapper
        )

    except ImportError:
        pass  # urllib3 not installed

    _hooks_installed = True
    return True


def uninstall_http_hooks() -> None:
    """
    Uninstall HTTP hooks.

    Note: wrapt patches cannot be fully undone, but we mark as uninstalled.
    """
    global _hooks_installed
    _hooks_installed = False


def is_http_hooks_installed() -> bool:
    """Check if HTTP hooks are installed."""
    return _hooks_installed
