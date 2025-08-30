from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, Protocol

from .context import Context
from .primitives import BaseDerived, Effect, _equal, _pulled

type AsyncFunction[T] = Callable[[], Coroutine[Any, Any, T]]


class TaskFactory(Protocol):
    def __call__[T](self, func: AsyncFunction[T], /) -> Awaitable[T]: ...


def default_task_factory[T](async_function: AsyncFunction[T]):
    from asyncio import ensure_future

    return ensure_future(async_function())


class AsyncEffect[T](Effect[Awaitable[T]]):
    def __init__(self, fn: Callable[[], Awaitable[T]], call_immediately=True, *, context: Context | None = None, task_factory: TaskFactory = default_task_factory):
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

    def __init__(self, fn: Callable[[], Awaitable[T]], check_equality=True, *, context: Context | None = None, task_factory: TaskFactory = default_task_factory):
        super().__init__(context=context)
        self.fn = fn
        self._check_equality = check_equality
        self._value = self.UNSET
        self.start: TaskFactory = task_factory
        self._call_task: Awaitable[T] | None = None
        self._sync_dirty_deps_task: Awaitable[None] | None = None

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

    async def __sync_dirty_deps(self):
        try:
            current_computations = self.context.leaf.current_computations
            for dep in self.dependencies:
                if isinstance(dep, BaseDerived) and dep not in current_computations:
                    if isinstance(dep, AsyncDerived):
                        await dep._sync_dirty_deps()  # noqa: SLF001
                        if dep.dirty:
                            await dep()
                    elif dep.dirty:
                        dep()
        finally:
            self._sync_dirty_deps_task = None

    def _sync_dirty_deps(self):
        if self._sync_dirty_deps_task is not None:
            return self._sync_dirty_deps_task
        task = self._sync_dirty_deps_task = self.start(self.__sync_dirty_deps)
        return task

    async def _call_async(self):
        self.track()
        await self._sync_dirty_deps()
        try:
            if self.dirty:
                await self.recompute()
            return self._value
        finally:
            self._call_task = None

    def __call__(self) -> Awaitable[T]:
        if self._call_task is not None:
            return self._call_task
        task = self._call_task = self.start(self._call_async)

        class Future:
            def __await__(_):  # noqa: N805  # type: ignore
                self.track()
                return task.__await__()

        return Future()

    def trigger(self):
        self.dirty = True
        if _pulled(self):
            return self()

    def invalidate(self):
        self.trigger()
