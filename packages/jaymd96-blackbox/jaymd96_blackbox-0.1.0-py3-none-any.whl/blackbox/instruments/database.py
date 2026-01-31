"""
Database query instrumentation.

Captures:
- SQLAlchemy queries via event listeners
- Generic query logging via connection wrappers
"""

import time
from typing import Any, Callable

from ..collector import get_collector, BreadcrumbType


# Track installed hooks
_sqlalchemy_hooks_installed = False


def _truncate_query(query: str, max_length: int = 100) -> str:
    """Truncate SQL query for display."""
    query = ' '.join(query.split())  # Normalize whitespace
    if len(query) <= max_length:
        return query
    return query[:max_length - 3] + "..."


def _format_query_type(query: str) -> str:
    """Extract query type from SQL."""
    query_upper = query.strip().upper()
    for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'BEGIN', 'COMMIT', 'ROLLBACK']:
        if query_upper.startswith(keyword):
            return keyword
    return "SQL"


def install_sqlalchemy_hooks() -> bool:
    """
    Install SQLAlchemy event listeners for query tracking.

    Returns True if installed, False if SQLAlchemy not available.
    """
    global _sqlalchemy_hooks_installed

    if _sqlalchemy_hooks_installed:
        return True

    try:
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            start_times = conn.info.get('query_start_time', [])
            if start_times:
                start_time = start_times.pop()
                duration = time.time() - start_time
            else:
                duration = None

            query_type = _format_query_type(statement)
            message = f"{query_type}: {_truncate_query(statement)}"

            # Try to get table name
            table = None
            statement_upper = statement.upper()
            for keyword in ['FROM', 'INTO', 'UPDATE', 'TABLE']:
                if keyword in statement_upper:
                    parts = statement_upper.split(keyword)
                    if len(parts) > 1:
                        table_part = parts[1].strip().split()[0]
                        table = table_part.strip('`"[]')
                        break

            data = {
                "query_type": query_type,
                "query": statement[:500],  # Store more in data
                "executemany": executemany,
            }
            if table:
                data["table"] = table
            if parameters:
                # Don't store full params (may contain sensitive data)
                data["param_count"] = len(parameters) if isinstance(parameters, (list, tuple, dict)) else 1

            get_collector().add_breadcrumb(
                type=BreadcrumbType.DB,
                category="sqlalchemy",
                message=message,
                data=data,
                duration=duration,
            )

        @event.listens_for(Engine, "handle_error")
        def handle_error(exception_context):
            message = f"DB ERROR: {type(exception_context.original_exception).__name__}"

            get_collector().add_breadcrumb(
                type=BreadcrumbType.DB,
                category="sqlalchemy_error",
                message=message,
                data={
                    "error": str(exception_context.original_exception),
                    "error_type": type(exception_context.original_exception).__name__,
                    "statement": str(exception_context.statement)[:200] if exception_context.statement else None,
                },
            )

        _sqlalchemy_hooks_installed = True
        return True

    except ImportError:
        return False


def install_sqlite3_hooks() -> bool:
    """
    Install sqlite3 connection wrapper for query tracking.

    Returns True if installed, False on failure.
    """
    try:
        import sqlite3

        _original_execute = sqlite3.Cursor.execute
        _original_executemany = sqlite3.Cursor.executemany

        def traced_execute(self, sql, parameters=()):
            start_time = time.time()
            try:
                result = _original_execute(self, sql, parameters)
                duration = time.time() - start_time

                query_type = _format_query_type(sql)
                message = f"{query_type}: {_truncate_query(sql)}"

                get_collector().add_breadcrumb(
                    type=BreadcrumbType.DB,
                    category="sqlite3",
                    message=message,
                    data={"query_type": query_type, "query": sql[:500]},
                    duration=duration,
                )

                return result
            except Exception as e:
                duration = time.time() - start_time

                get_collector().add_breadcrumb(
                    type=BreadcrumbType.DB,
                    category="sqlite3_error",
                    message=f"DB ERROR: {type(e).__name__}",
                    data={"error": str(e), "query": sql[:200]},
                    duration=duration,
                )
                raise

        def traced_executemany(self, sql, seq_of_parameters):
            start_time = time.time()
            try:
                result = _original_executemany(self, sql, seq_of_parameters)
                duration = time.time() - start_time

                query_type = _format_query_type(sql)
                count = len(list(seq_of_parameters)) if hasattr(seq_of_parameters, '__len__') else '?'
                message = f"{query_type} (x{count}): {_truncate_query(sql)}"

                get_collector().add_breadcrumb(
                    type=BreadcrumbType.DB,
                    category="sqlite3",
                    message=message,
                    data={"query_type": query_type, "query": sql[:500], "count": count},
                    duration=duration,
                )

                return result
            except Exception as e:
                get_collector().add_breadcrumb(
                    type=BreadcrumbType.DB,
                    category="sqlite3_error",
                    message=f"DB ERROR: {type(e).__name__}",
                    data={"error": str(e), "query": sql[:200]},
                )
                raise

        sqlite3.Cursor.execute = traced_execute
        sqlite3.Cursor.executemany = traced_executemany

        return True

    except Exception:
        return False


def install_database_hooks() -> dict[str, bool]:
    """
    Install all available database hooks.

    Returns dict of hook name -> success.
    """
    return {
        "sqlalchemy": install_sqlalchemy_hooks(),
        "sqlite3": install_sqlite3_hooks(),
    }


def is_sqlalchemy_hooks_installed() -> bool:
    """Check if SQLAlchemy hooks are installed."""
    return _sqlalchemy_hooks_installed
