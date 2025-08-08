from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from functools import partial
from inspect import currentframe
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .primitives import BaseComputation, Batch


class Context:
    def __init__(self):
        self.batches: list[Batch] = []
        self._untracked = False

    @property
    def current_computations(self) -> list[BaseComputation]:
        if self._untracked:
            return []

        from .primitives import BaseComputation

        computations = []
        # Start from frame 1 to skip the current property's own frame
        frame = currentframe()
        while frame:
            # Check if the frame is from a BaseComputation instance method
            # that belongs to this context.
            if frame.f_code.co_name in ("trigger", "recompute") and "self" in frame.f_locals and isinstance(frame.f_locals["self"], BaseComputation) and frame.f_locals["self"].context is self:
                computations.append(frame.f_locals["self"])
            frame = frame.f_back

        # The frames are walked from innermost to outermost, so we reverse
        # to get the natural order of [outer, inner].
        computations.reverse()
        return computations

    def schedule_callbacks(self, callbacks: Iterable[BaseComputation]):
        if self.batches:
            self.batches[-1].callbacks.update(callbacks)

    @contextmanager
    def enter(self, computation: BaseComputation):
        old_dependencies = {*computation.dependencies}
        computation.dispose()
        # Note: We are no longer manually managing current_computations stack here
        # The stack is now dynamically inferred from the call frames.
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
        old_untracked = self._untracked
        self._untracked = True
        try:
            yield
        finally:
            self._untracked = old_untracked


def new_context():
    return Context()


default_context = new_context()

from .primitives import Batch, Effect, Signal
