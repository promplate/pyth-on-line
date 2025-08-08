from collections.abc import Awaitable, Callable, Coroutine
from contextvars import ContextVar
from typing import Any

from .context import Context
from .primitives import Effect, default_context

current = ContextVar[Context]("current async context")


def child_context(parent: Context):
    return Context(parent.current_computations[:], parent.batches)


type AsyncFunction[T] = Callable[[], Coroutine[Any, Any, T]]

type TaskFactory[T] = Callable[[AsyncFunction[T]], Awaitable[T]]


def default_task_factory[T](async_function: AsyncFunction[T]):
    from asyncio import ensure_future

    return ensure_future(async_function())


class AsyncEffect[T](Effect[Awaitable[T]]):
    def __init__(self, fn: Callable[[], Awaitable[T]], call_immediately=True, *, context: Context | None = None, task_factory: TaskFactory[T] = default_task_factory):
        self.start = task_factory
        self.base_context = context or default_context
        Effect.__init__(self, fn, call_immediately)
        del self.context

    async def _run_in_context(self):
        new = child_context(current.get(self.base_context))
        current.set(new)
        with new.enter(self):
            return await self._fn()

    def trigger(self):
        return self.start(self._run_in_context)
