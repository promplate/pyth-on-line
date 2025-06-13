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
        """
        Adds the given computations as callbacks to the most recent batch in the context.
        
        Args:
            callbacks: An iterable of computations to be scheduled as callbacks in the latest batch.
        """
        self.batches[-1].callbacks.update(callbacks)

    @contextmanager
    def enter(self, computation: BaseComputation):
        """
        A context manager that temporarily adds a computation to the current computations stack.
        
        Ensures the computation is disposed before entering and removed after exiting the context, maintaining stack integrity.
        """
        computation.dispose()
        self.current_computations.append(computation)
        try:
            yield
        finally:
            last = self.current_computations.pop()
            assert last is computation  # sanity check

    @property
    def batch(self):
        """
        Returns a partial constructor for creating Batch instances bound to this context.
        
        Use this property to instantiate Batch objects that are automatically associated with the current Context.
        """
        return partial(Batch, context=self)

    @property
    def signal(self):
        """
        Returns a partially applied Signal constructor bound to this context.
        
        Use this property to create Signal instances associated with the current Context.
        """
        return partial(Signal, context=self)

    @property
    def effect(self):
        """
        Returns a partially applied Effect constructor bound to this context.
        
        Use this property to create new Effect instances associated with the current Context.
        """
        return partial(Effect, context=self)

    @contextmanager
    def untrack(self):
        """
        A context manager that temporarily disables tracking of computations.
        
        Within the managed block, the current computations stack is cleared and restored upon exit, allowing code to run without being registered as a dependency of any computation.
        """
        computations = self.current_computations[:]
        self.current_computations.clear()
        try:
            yield
        finally:
            self.current_computations[:] = computations


def new_context():
    """
    Creates and returns a new Context instance with empty computation and batch lists.
    
    Returns:
        Context: A new context with no current computations or batches.
    """
    return Context([], [])


default_context = new_context()

from .primitives import Batch, Effect, Signal
