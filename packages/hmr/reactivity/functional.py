from collections.abc import Callable
from functools import wraps
from typing import Protocol, overload

from .helpers import Memoized, MemoizedMethod, MemoizedProperty
from .primitives import Batch, Effect, Signal


class Getter[T](Protocol):
    def __call__(self, track=True) -> T:
        """
        Returns the current value of the signal.

        Args:
                track: If True, tracks dependencies for reactive updates. Defaults to True.

        Returns:
                The current value stored in the signal.
        """
        ...


class Setter[T](Protocol):
    def __call__(self, value: T) -> bool:
        """
        Sets the signal's value and notifies dependents if the value has changed.

        Args:
                value: The new value to assign to the signal.

        Returns:
                True if the value was updated and dependents were notified; False if the value was unchanged.
        """
        ...


def create_signal[T](initial_value: T = None, check_equality=True) -> tuple[Getter[T], Setter[T]]:
    """
    Creates a reactive signal with getter and setter functions.

    Args:
        initial_value: The initial value of the signal.
        check_equality: If True, updates only trigger when the value changes.

    Returns:
        A tuple containing a getter function to access the signal's value and a setter function to update it.
    """
    signal = Signal(initial_value, check_equality)
    return signal.get, signal.set


def create_effect[T](fn: Callable[[], T], call_immediately=True):
    """
    Creates a reactive effect that runs the provided function when its dependencies change.

    Args:
        fn: A function to execute reactively when its dependencies are updated.
        call_immediately: If True, the effect runs immediately upon creation.

    Returns:
        An Effect instance managing the reactive execution of the function.
    """
    return Effect(fn, call_immediately)


def create_memo[T](fn: Callable[[], T]):
    """
    Creates a memoized reactive computation based on the provided function.

    The returned object caches the result of `fn` and automatically updates when its reactive dependencies change.

    Args:
        fn: A function whose result should be memoized and tracked reactively.

    Returns:
        A Memoized instance representing the reactive, cached computation.
    """
    return Memoized(fn)


def memoized_property[T, I](method: Callable[[I], T]):
    """
    Wraps a method as a memoized property.

    Returns a MemoizedProperty that caches the result of the method for each instance, recomputing only when dependencies change.
    """
    return MemoizedProperty(method)


def memoized_method[T, I](method: Callable[[I], T]):
    """
    Wraps an instance method with memoization, caching its result per instance.

    Args:
        method: The instance method to be memoized.

    Returns:
        A MemoizedMethod object that caches the method's result for each instance.
    """
    return MemoizedMethod(method)


@overload
def batch() -> Batch:
    """
    Creates a new batch context manager for grouping reactive updates.

    Returns:
        A Batch instance to be used as a context manager.
    """


@overload
def batch[**P, T](func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator that executes the decorated function within a reactive batch context.

    All reactive updates triggered during the function's execution are grouped and applied together,
    minimizing redundant computations and side effects.

    Returns:
        A wrapped function that runs within a batch context.
    """


def batch[**P, T](func: Callable[P, T] | None = None) -> Callable[P, T] | Batch:
    """
    Provides a batching context for reactive updates, either as a context manager or a function decorator.

    When used as a context manager, groups reactive updates within its scope to minimize redundant computations.
    When used as a decorator, ensures the decorated function executes within a batch context.
    """
    if func is not None:

        @wraps(func)
        def wrapped(*args, **kwargs):
            with Batch():
                return func(*args, **kwargs)

        return wrapped

    return Batch()
