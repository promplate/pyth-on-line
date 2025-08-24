from collections.abc import Awaitable, Callable, Coroutine
from typing import Any

from .context import Context
from .primitives import Effect

type AsyncFunction[T] = Callable[[], Coroutine[Any, Any, T]]

type TaskFactory[T] = Callable[[AsyncFunction[T]], Awaitable[T]]


def default_task_factory[T](async_function: AsyncFunction[T]):
    from asyncio import ensure_future

    return ensure_future(async_function())


class AsyncEffect[T](Effect[Awaitable[T]]):
    def __init__(self, fn: Callable[[], Awaitable[T]], call_immediately=True, *, context: Context | None = None, task_factory: TaskFactory[T] = default_task_factory):
        Effect.__init__(self, fn, call_immediately, context=context)
        self.start = task_factory

    async def _run_in_context(self):
        self.context.fork()
        with self.context.get_current_context().enter(self):
            return await self._fn()

    def trigger(self):
        return self.start(self._run_in_context)
