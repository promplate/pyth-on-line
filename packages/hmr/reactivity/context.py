from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .primitives import BaseComputation


@dataclass(slots=True, eq=False)
class StackFrame[T]:
    value: T
    parent: StackFrame[T] | None = None
    depth: int = 1
    active: bool = True

    def __init__(self, value: T, parent: StackFrame[T] | None = None):
        self.value = value
        self.parent = parent
        self.depth = 1 if parent is None else parent.depth + 1
        self.active = True

    def __iter__(self) -> Iterator[T]:
        values = []
        frame: StackFrame[T] | None = self
        while frame is not None:
            values.append(frame.value)
            frame = frame.parent
        return reversed(values)

    def __contains__(self, value: object) -> bool:
        frame: StackFrame[T] | None = self
        while frame is not None:
            if frame.value is value:
                return True
            frame = frame.parent
        return False


class Context:
    def __init__(self):
        self._current_computations: ContextVar[StackFrame[BaseComputation] | None] = ContextVar("current computations", default=None)
        self._batches: ContextVar[StackFrame[Batch] | None] = ContextVar("batches", default=None)

    def _active_frames[T](self, frame: StackFrame[T] | None) -> Iterator[StackFrame[T]]:
        while frame is not None:
            if frame.active:
                yield frame
            frame = frame.parent

    @property
    def current_computations(self) -> list[BaseComputation]:
        frame = self._current_computations.get()
        return [item.value for item in reversed([*self._active_frames(frame)])]

    @property
    def current_computation(self) -> BaseComputation | None:
        frame = self._current_computations.get()
        return next((item.value for item in self._active_frames(frame)), None)

    def is_computing(self, computation: BaseComputation) -> bool:
        return any(item.value is computation for item in self._active_frames(self._current_computations.get()))

    @property
    def current_batch(self) -> Batch | None:
        frame = self._batches.get()
        return next((item.value for item in self._active_frames(frame)), None)

    @property
    def batch_depth(self) -> int:
        frame = self._batches.get()
        return sum(1 for _ in self._active_frames(frame))

    def schedule_callbacks(self, callbacks: Iterable[BaseComputation]):
        batch = self.current_batch
        assert batch is not None
        batch.callbacks.update(callbacks)

    @contextmanager
    def enter(self, computation: BaseComputation):
        old_dependencies = {*computation.dependencies}
        computation.dispose()
        frame = StackFrame(computation, self._current_computations.get())
        token = self._current_computations.set(frame)
        try:
            yield
        except BaseException:
            # For backward compatibility, we restore old dependencies only if some dependencies are lost after an exception.
            # This behavior may be configurable in the future.
            if computation.dependencies.issubset(old_dependencies):
                for dep in old_dependencies:
                    dep.subscribers.add(computation)
                computation.dependencies.update(old_dependencies)
            raise
        else:
            if not computation.dependencies and (strategy := computation.reactivity_loss_strategy) != "ignore":
                if strategy == "restore" and old_dependencies:
                    for dep in old_dependencies:
                        dep.subscribers.add(computation)
                    computation.dependencies.update(old_dependencies)
                    return
                from pathlib import Path
                from sysconfig import get_path
                from warnings import warn

                msg = "lost all its dependencies" if old_dependencies else "has no dependencies"
                warn(f"{computation} {msg} and will never be auto-triggered.", RuntimeWarning, skip_file_prefixes=(str(Path(__file__).parent), s := get_path("stdlib"), str(Path(s).resolve())))
        finally:
            assert self._current_computations.get() is frame
            frame.active = False
            self._current_computations.reset(token)

    @property
    def batch(self):
        return partial(Batch, context=self)

    @property
    def signal(self):
        return partial(Signal, context=self)

    @property
    def effect(self):
        return partial(Effect, context=self)

    @property
    def derived(self):
        return partial(Derived, context=self)

    @property
    def async_effect(self):
        return partial(AsyncEffect, context=self)

    @property
    def async_derived(self):
        return partial(AsyncDerived, context=self)

    @contextmanager
    def untrack(self):
        token = self._current_computations.set(None)
        try:
            yield
        finally:
            self._current_computations.reset(token)

    @contextmanager
    def enter_batch(self, batch: Batch):
        frame = StackFrame(batch, self._batches.get())
        token = self._batches.set(frame)
        try:
            yield
        finally:
            assert self._batches.get() is frame
            frame.active = False
            self._batches.reset(token)

    @property
    def leaf(self):
        return self

    def fork(self) -> None:
        # Async computations start a fresh tracking scope. Call sites are
        # tracked before their task is spawned; inheriting the caller's active
        # frame here would make the task body collect against that caller too.
        self._current_computations.set(None)
        self._batches.set(None)


def new_context():
    return Context()


default_context = new_context()

from .async_primitives import AsyncDerived, AsyncEffect
from .primitives import Batch, Derived, Effect, Signal
