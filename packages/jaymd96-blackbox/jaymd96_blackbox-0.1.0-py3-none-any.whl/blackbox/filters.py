"""
Filters for collapsing noise and focusing on relevant code.

Allows users to:
- Focus on specific packages
- Collapse stdlib/framework internals
- Limit depth
"""

import sys
import os
from pathlib import Path
from typing import Callable
from dataclasses import dataclass, field


# Known framework/library prefixes to collapse
KNOWN_FRAMEWORKS = {
    'django': 'django',
    'flask': 'flask',
    'fastapi': 'fastapi',
    'starlette': 'starlette',
    'requests': 'requests',
    'urllib3': 'urllib3',
    'sqlalchemy': 'sqlalchemy',
    'pytest': 'pytest',
    'unittest': 'unittest',
    'asyncio': 'asyncio',
    'concurrent': 'concurrent',
    'multiprocessing': 'multiprocessing',
    'threading': 'threading',
}


@dataclass
class Filter:
    """
    Filter configuration for stack frames.

    Attributes:
        focus: Only show frames from these packages (e.g., ['mypackage'])
        collapse: Collapse frames from these packages into summaries
        show_stdlib: Whether to show stdlib frames (default: collapse them)
        max_depth: Maximum number of frames to show
        exclude_patterns: File patterns to always exclude
    """
    focus: list[str] = field(default_factory=list)
    collapse: list[str] = field(default_factory=list)
    show_stdlib: bool = False
    max_depth: int | None = None
    exclude_patterns: list[str] = field(default_factory=lambda: [
        '**/site-packages/pip/**',
        '**/site-packages/setuptools/**',
        '**/__pycache__/**',
        '**/blackbox/**',  # Filter out blackbox internals
        '**/runpy.py',     # Filter out runpy
    ])

    def __post_init__(self):
        # Auto-add known frameworks to collapse list
        if not self.collapse:
            self.collapse = list(KNOWN_FRAMEWORKS.keys())

    def should_show_frame(self, filename: str, module: str | None = None) -> bool:
        """Determine if a frame should be shown (not collapsed)."""
        # Always exclude certain patterns
        for pattern in self.exclude_patterns:
            if self._matches_pattern(filename, pattern):
                return False

        # If focus is specified, only show matching frames
        if self.focus:
            return self._matches_any(filename, module, self.focus)

        # Check if it's stdlib
        if self._is_stdlib(filename):
            return self.show_stdlib

        # Check if it should be collapsed
        if self._matches_any(filename, module, self.collapse):
            return False

        return True

    def categorize_frame(self, filename: str, module: str | None = None) -> str | None:
        """
        Categorize a frame for collapse grouping.

        Returns the category name (e.g., 'stdlib', 'django') or None if should be shown.
        """
        if self.should_show_frame(filename, module):
            return None

        if self._is_stdlib(filename):
            return 'stdlib'

        # Check known frameworks
        for framework, name in KNOWN_FRAMEWORKS.items():
            if self._matches_any(filename, module, [framework]):
                return name

        # Generic site-packages
        if 'site-packages' in filename:
            # Try to extract package name
            parts = filename.split('site-packages')
            if len(parts) > 1:
                pkg_path = parts[1].strip(os.sep)
                pkg_name = pkg_path.split(os.sep)[0] if pkg_path else 'third-party'
                return pkg_name

        return 'other'

    def _is_stdlib(self, filename: str) -> bool:
        """Check if a file is part of the standard library."""
        # Get stdlib path
        stdlib_path = os.path.dirname(os.__file__)

        try:
            # Resolve to handle symlinks
            resolved = str(Path(filename).resolve())
            stdlib_resolved = str(Path(stdlib_path).resolve())

            # Check if file is under stdlib
            if resolved.startswith(stdlib_resolved):
                return True

            # Also check for frozen modules
            if filename.startswith('<frozen'):
                return True

        except (OSError, ValueError):
            pass

        return False

    def _matches_any(
        self,
        filename: str,
        module: str | None,
        patterns: list[str]
    ) -> bool:
        """Check if filename or module matches any of the patterns."""
        for pattern in patterns:
            # Check module name
            if module and (module == pattern or module.startswith(pattern + '.')):
                return True

            # Check filename
            if pattern in filename:
                return True

            # Check as path component
            if os.sep + pattern + os.sep in filename:
                return True
            if filename.endswith(os.sep + pattern + '.py'):
                return True

        return False

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches a glob-like pattern."""
        # Simple glob matching
        if '**' in pattern:
            # Convert to simple contains check
            parts = pattern.split('**')
            return all(p.strip('/') in filename for p in parts if p.strip('/'))
        elif '*' in pattern:
            # Single wildcard
            parts = pattern.split('*')
            pos = 0
            for part in parts:
                if part:
                    idx = filename.find(part, pos)
                    if idx == -1:
                        return False
                    pos = idx + len(part)
            return True
        else:
            return pattern in filename


def filter_frames(
    frames: list[dict],
    filter_config: Filter
) -> tuple[list[dict], dict[str, int]]:
    """
    Filter stack frames according to configuration.

    Returns:
        (filtered_frames, collapsed_counts)

    collapsed_counts is a dict of category -> count for collapsed frames.
    """
    filtered = []
    collapsed: dict[str, int] = {}

    for frame in frames:
        filename = frame.get('filename', '')
        module = frame.get('module')

        category = filter_config.categorize_frame(filename, module)

        if category is None:
            # Show this frame
            filtered.append(frame)
        else:
            # Collapse into category
            collapsed[category] = collapsed.get(category, 0) + 1

    # Apply max_depth if specified
    if filter_config.max_depth and len(filtered) > filter_config.max_depth:
        # Keep first and last frames, collapse middle
        if filter_config.max_depth >= 2:
            head = filtered[:filter_config.max_depth // 2]
            tail = filtered[-(filter_config.max_depth - len(head)):]
            middle_count = len(filtered) - len(head) - len(tail)
            collapsed['...'] = middle_count
            filtered = head + tail
        else:
            filtered = filtered[:filter_config.max_depth]

    return filtered, collapsed
