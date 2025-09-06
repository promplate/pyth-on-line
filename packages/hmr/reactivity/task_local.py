"""
Task-local storage implementation to replace contextvars.
This provides a ContextVar-like interface using asyncio task-local storage.
"""

from __future__ import annotations

import asyncio
import weakref


class TaskContextVar[T]:
    """
    A task-local context variable that mimics contextvars.ContextVar behavior
    but uses asyncio task-local storage instead.
    """

    def __init__(self, name: str, *, default: T | None = None):
        self.name = name
        self.default = default
        # Use WeakKeyDictionary to avoid memory leaks when tasks complete
        self._storage: weakref.WeakKeyDictionary[asyncio.Task, T] = weakref.WeakKeyDictionary()

    def get(self, default: T | None = None) -> T | None:
        """Get the value for the current task."""
        try:
            task = asyncio.current_task()
            if task is None:
                # Not in an async context, return default
                return default if default is not None else self.default

            return self._storage.get(task, default if default is not None else self.default)
        except RuntimeError:
            # Not in an async context (e.g., no event loop)
            return default if default is not None else self.default

    def set(self, value: T) -> None:
        """Set the value for the current task."""
        try:
            task = asyncio.current_task()
            if task is None:
                # Not in an async context, ignore the set operation
                # This matches contextvars behavior in sync contexts
                return

            self._storage[task] = value
        except RuntimeError:
            # Not in an async context, ignore the set operation
            pass
