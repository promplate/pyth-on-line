from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from .primitives import BaseComputation, Batch


class Context(NamedTuple):
    current_computations: list[BaseComputation] = []  # noqa: RUF012
    batches: list[Batch] = []  # noqa: RUF012

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


default_context = Context()
