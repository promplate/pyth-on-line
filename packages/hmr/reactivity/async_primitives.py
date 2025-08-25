from collections.abc import Awaitable, Callable, Coroutine
from typing import Any

from .context import Context
from .primitives import BaseDerived, Effect, _equal, _pulled

type AsyncFunction[T] = Callable[[], Coroutine[Any, Any, T]]

type TaskFactory[T] = Callable[[AsyncFunction[T]], Awaitable[T]]


def default_task_factory[T](async_function: AsyncFunction[T]):
    from asyncio import ensure_future

    return ensure_future(async_function())


class AsyncEffect[T](Effect[Awaitable[T]]):
    def __init__(self, fn: AsyncFunction[T], call_immediately=True, *, context: Context | None = None, task_factory: TaskFactory[T] = default_task_factory):
        self.start = task_factory
        Effect.__init__(self, fn, call_immediately, context=context)

    async def _run_in_context(self):
        self.context.fork()
        with self._enter():
            return await self._fn()

    def trigger(self):
        return self.start(self._run_in_context)


class AsyncDerived[T](BaseDerived[Awaitable[T]]):
    UNSET: T = object()  # type: ignore

    def __init__(self, fn: AsyncFunction[T], check_equality=True, *, context: Context | None = None, task_factory: TaskFactory[T] = default_task_factory):
        super().__init__(context=context)
        self.fn = fn
        self._check_equality = check_equality
        self._value = self.UNSET
        self.start = task_factory

    async def _run_in_context(self):
        self.context.fork()
        with self._enter():
            return await self.fn()

    async def recompute(self):
        value = await self._run_in_context()
        self.dirty = False
        if self._check_equality:
            if _equal(value, self._value):
                return
            elif self._value is self.UNSET:  # do not notify on first set
                self._value = value
                return
        self._value = value
        self.notify()

    async def _call_async(self):
        self.track()
        self._sync_dirty_deps()
        if self.dirty:
            await self.recompute()

        return self._value

    def __call__(self):
        return self.start(self._call_async)

    def trigger(self):
        self.dirty = True
        if _pulled(self):
            return self()

    def invalidate(self):
        self.trigger()
