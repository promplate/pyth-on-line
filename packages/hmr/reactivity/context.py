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
                warn(f"{computation} {msg} and will never be auto-triggered.", RuntimeWarning, skip_file_prefixes=(str(Path(__file__).parent), str(Path(get_path("stdlib")).resolve())))
        finally:
            last = self.current_computations.pop()
            # assert last is computation  # sanity check

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
        computations = self.current_computations[:]
        self.current_computations.clear()
        try:
            yield
        finally:
            self.current_computations[:] = computations

    @property
    def leaf(self):
        return self.async_execution_context.get() or self

    def fork(self):
        self.async_execution_context.set(Context(self.current_computations[:], self.batches[:], self.async_execution_context))


def new_context():
    return Context([], [], async_execution_context=ContextVar("current context", default=None))


default_context = new_context()

from .async_primitives import AsyncDerived, AsyncEffect
from .primitives import Batch, Derived, Effect, Signal
