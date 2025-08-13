from __future__ import annotations

import sys
from collections.abc import Iterable
from contextlib import contextmanager
from functools import partial
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from .primitives import BaseComputation


class Context(NamedTuple):
    batches: list[Batch]
    no_track: list

    def schedule_callbacks(self, callbacks: Iterable[BaseComputation]):
        self.batches[-1].callbacks.update(callbacks)

    def iter_computations(self, extra_depth=0):
        frame = sys._getframe(extra_depth + 1)  # noqa: SLF001
        while frame is not None:
            with self.untrack():
                computation = frame.f_locals.get("--computation-context")
            if computation is not None:
                yield computation
            frame = frame.f_back

    @property
    def last_computation(self):
        for comp in self.iter_computations(extra_depth=1):
            if comp.context is self:
                return comp

    @property
    def current_computations(self):
        return [*reversed([c for c in self.iter_computations(extra_depth=1) if c.context is self])]

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
        self.no_track.append(None)
        try:
            yield
        finally:
            self.no_track.pop()


def new_context():
    return Context([], [])


default_context = new_context()

from .primitives import Batch, Effect, Signal
