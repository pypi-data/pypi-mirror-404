"""
Environment and configuration access tracking.

Captures:
- Environment variable reads (os.environ, os.getenv)
- Config file access patterns
- Sensitive variable detection
"""

import os
import functools
from typing import Any, Callable

from ..collector import get_collector, BreadcrumbType


# Track state
_env_hooks_installed = False
_original_getenv: Callable | None = None
_original_environ_getitem: Callable | None = None


# Sensitive variable patterns (partial matches)
SENSITIVE_PATTERNS = [
    'password', 'passwd', 'pwd',
    'secret', 'key', 'token',
    'auth', 'credential', 'cred',
    'api_key', 'apikey',
    'private', 'priv',
    'access_token', 'refresh_token',
    'jwt', 'bearer',
    'db_pass', 'database_password',
    'aws_secret', 'azure_secret', 'gcp_secret',
    'encryption', 'decrypt',
    'ssh', 'pem', 'cert',
]


def _is_sensitive(name: str) -> bool:
    """Check if a variable name looks sensitive."""
    name_lower = name.lower()
    for pattern in SENSITIVE_PATTERNS:
        if pattern in name_lower:
            return True
    return False


def _mask_value(value: str | None, is_sensitive: bool) -> str:
    """Mask sensitive values, show partial for non-sensitive."""
    if value is None:
        return "<not set>"

    if is_sensitive:
        return "<REDACTED>"

    # Show partial value for non-sensitive
    if len(value) <= 20:
        return value
    return value[:17] + "..."


def _record_env_access(name: str, value: str | None, method: str) -> None:
    """Record an environment variable access."""
    is_sensitive = _is_sensitive(name)
    masked = _mask_value(value, is_sensitive)

    message = f"ENV[{name}] = {masked}"
    if value is None:
        message = f"ENV[{name}] → not set"

    data = {
        "variable": name,
        "method": method,
        "is_set": value is not None,
        "is_sensitive": is_sensitive,
    }

    # Only include value for non-sensitive vars
    if not is_sensitive and value is not None:
        data["value"] = value[:100] if len(value) > 100 else value

    get_collector().add_breadcrumb(
        type=BreadcrumbType.CONFIG,
        category="environment",
        message=message,
        data=data,
    )


def install_env_hooks() -> bool:
    """
    Install hooks to track environment variable access.

    Returns True if installed successfully.
    """
    global _env_hooks_installed, _original_getenv, _original_environ_getitem

    if _env_hooks_installed:
        return True

    try:
        # Hook os.getenv
        _original_getenv = os.getenv

        @functools.wraps(os.getenv)
        def traced_getenv(key, default=None):
            result = _original_getenv(key, default)
            # Record the access (use actual value from environ for accuracy)
            actual_value = os.environ.get(key)
            _record_env_access(key, actual_value, "getenv")
            return result

        os.getenv = traced_getenv

        # Hook os.environ.__getitem__
        _original_environ_getitem = os.environ.__class__.__getitem__

        def traced_getitem(self, key):
            try:
                result = _original_environ_getitem(self, key)
                _record_env_access(key, result, "environ[]")
                return result
            except KeyError:
                _record_env_access(key, None, "environ[]")
                raise

        # Note: Can't easily patch __getitem__ on os._Environ
        # Instead, we'll rely on getenv hook and audit hooks for 'open'

        _env_hooks_installed = True
        return True

    except Exception:
        return False


def uninstall_env_hooks() -> None:
    """Uninstall environment hooks."""
    global _env_hooks_installed, _original_getenv

    if _original_getenv is not None:
        os.getenv = _original_getenv
        _original_getenv = None

    _env_hooks_installed = False


def is_env_hooks_installed() -> bool:
    """Check if environment hooks are installed."""
    return _env_hooks_installed


def get_env_snapshot() -> dict:
    """
    Get a snapshot of interesting environment variables.

    Returns dict with categorized env vars (sensitive values masked).
    """
    snapshot = {
        "python": {},
        "path": {},
        "system": {},
        "application": {},
        "sensitive_count": 0,
    }

    for key, value in os.environ.items():
        is_sensitive = _is_sensitive(key)
        masked = _mask_value(value, is_sensitive)

        if is_sensitive:
            snapshot["sensitive_count"] += 1

        # Categorize
        key_upper = key.upper()
        if key_upper.startswith('PYTHON') or key_upper in ('VIRTUAL_ENV', 'CONDA_DEFAULT_ENV', 'PYTHONPATH'):
            snapshot["python"][key] = masked
        elif 'PATH' in key_upper:
            snapshot["path"][key] = masked
        elif key_upper in ('HOME', 'USER', 'SHELL', 'TERM', 'LANG', 'LC_ALL', 'TZ', 'PWD', 'HOSTNAME'):
            snapshot["system"][key] = masked
        # Skip the rest to avoid noise

    return snapshot


# Config file patterns to watch (for audit hook enhancement)
CONFIG_FILE_PATTERNS = [
    '.env',
    '.ini',
    '.cfg',
    '.conf',
    '.config',
    '.yaml',
    '.yml',
    '.json',
    '.toml',
    'settings',
    'config',
    'secrets',
]


def is_config_file(path: str) -> bool:
    """Check if a path looks like a config file."""
    path_lower = path.lower()
    for pattern in CONFIG_FILE_PATTERNS:
        if pattern in path_lower:
            return True
    return False
