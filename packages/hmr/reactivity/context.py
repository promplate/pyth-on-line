from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from contextvars import ContextVar
from functools import partial
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from .primitives import BaseComputation


class Context(NamedTuple):
    current_computations: list[BaseComputation]
    batches: list[Batch]
    async_execution_context: ContextVar[Context | None]

    def schedule_callbacks(self, callbacks: Iterable[BaseComputation]):
        self.batches[-1].callbacks.update(callbacks)

    @contextmanager
    def enter(self, computation: BaseComputation):
        old_dependencies = {*computation.dependencies}
        computation.dispose()
        self.current_computations.append(computation)
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
        finally:
            last = self.current_computations.pop()
            assert last is computation  # sanity check

    @property
    def batch(self):
        return partial(Batch, context=self)

    @property
    def signal(self):
        return partial(Signal, context=self)

    @property
    def effect(self):
        return partial(Effect, context=self)

    @contextmanager
    def untrack(self):
        computations = self.current_computations[:]
        self.current_computations.clear()
        try:
            yield
        finally:
            self.current_computations[:] = computations

    @property
    def current(self):
        return self.async_execution_context.get() or self

    def fork(self):
        self.async_execution_context.set(Context(self.current_computations[:], self.batches[:], self.async_execution_context))


def new_context():
    return Context([], [], async_execution_context=ContextVar("current context", default=None))


default_context = new_context()

from .primitives import Batch, Effect, Signal
