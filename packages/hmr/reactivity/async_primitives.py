from collections.abc import Awaitable, Callable, Coroutine
from sys import platform
from typing import Any, Protocol

from .context import Context
from .primitives import BaseDerived, Effect, _equal, _pulled

type AsyncFunction[T] = Callable[[], Coroutine[Any, Any, T]]


class TaskFactory(Protocol):
    def __call__[T](self, func: AsyncFunction[T], /) -> Awaitable[T]: ...


def default_task_factory[T](async_function: AsyncFunction[T]) -> Awaitable[T]:
    if platform == "emscripten":
        from asyncio import ensure_future

        return ensure_future(async_function())

    from sniffio import AsyncLibraryNotFoundError, current_async_library

    match current_async_library():
        case "asyncio":
            from asyncio import ensure_future

            return ensure_future(async_function())

        case "trio":
            from trio import Event
            from trio.lowlevel import spawn_system_task

            evt = Event()
            res: T
            exc: BaseException | None = None

            @spawn_system_task
            async def _():
                nonlocal res, exc
                try:
                    res = await async_function()
                except BaseException as e:
                    exc = e
                finally:
                    evt.set()

            class Future:  # An awaitable that can be awaited multiple times
                def __await__(self):
                    if not evt.is_set():
                        yield from evt.wait().__await__()
                    if exc is not None:
                        raise exc
                    return res  # noqa: F821

            return Future()

        case _ as other:
            raise AsyncLibraryNotFoundError(f"Only asyncio and trio are supported, not {other}")  # noqa: TRY003


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
        self._call_task: Awaitable[None] | None = None
        self._sync_dirty_deps_task: Awaitable[None] | None = None

    async def _run_in_context(self):
        self.context.fork()
        with self._enter():
            return await self.fn()

    async def recompute(self):
        value = await self._run_in_context()
        if self._call_task is not None:
            self.dirty = False  # If invalidated before this run completes, stay dirty.
        if self._check_equality:
            if _equal(value, self._value):
                return
            if self._value is self.UNSET:  # do not notify on first set
                self._value = value
                return
        self._value = value
        self.notify()

    async def __sync_dirty_deps(self):
        try:
            current_computations = self.context.leaf.current_computations
            for dep in tuple(self.dependencies):  # note: I don't know why but `self.dependencies` may shrink during iteration
                if isinstance(dep, BaseDerived) and dep not in current_computations:
                    if isinstance(dep, AsyncDerived):
                        await dep._sync_dirty_deps()  # noqa: SLF001
                        if dep.dirty:
                            await dep()
                    else:
                        await __class__.__sync_dirty_deps(dep)  # noqa: SLF001  # type: ignore
                        if dep.dirty:
                            dep()
        finally:
            self._sync_dirty_deps_task = None

    def _sync_dirty_deps(self):
        if self._sync_dirty_deps_task is not None:
            return self._sync_dirty_deps_task
        task = self._sync_dirty_deps_task = self.start(self.__sync_dirty_deps)
        return task

    async def _call_async(self):
        await self._sync_dirty_deps()
        try:
            if self.dirty:
                if self._call_task is not None:
                    await self._call_task
                else:
                    task = self._call_task = self.start(self.recompute)
                    await task
            return self._value
        finally:
            self._call_task = None

    def __call__(self):
        self.track()
        return self.start(self._call_async)

    def trigger(self):
        self.dirty = True
        self._call_task = None
        if _pulled(self):
            return self()

    def invalidate(self):
        self.trigger()
