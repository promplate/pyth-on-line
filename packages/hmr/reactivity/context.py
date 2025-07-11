from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from functools import partial
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from .primitives import BaseComputation


class Context(NamedTuple):
    current_computations: list[BaseComputation]
    batches: list[Batch]

    def schedule_callbacks(self, callbacks: Iterable[BaseComputation]):
        self.batches[-1].callbacks.update(callbacks)

    @contextmanager
    def enter(self, computation: BaseComputation):
        computation.dispose()
        self.current_computations.append(computation)
        try:
            yield
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


def new_context():
    return Context([], [])


default_context = new_context()

from .primitives import Batch, Effect, Signal
