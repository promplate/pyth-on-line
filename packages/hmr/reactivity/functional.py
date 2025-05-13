from collections.abc import Callable
from functools import wraps
from typing import Protocol, overload

from .helpers import Memoized, MemoizedMethod, MemoizedProperty
from .primitives import Batch, Effect, Signal


class Getter[T](Protocol):
    def __call__(self, track=True) -> T: ...


class Setter[T](Protocol):
    def __call__(self, value: T) -> bool: ...


def create_signal[T](initial_value: T = None, check_equality=True) -> tuple[Getter[T], Setter[T]]:
    signal = Signal(initial_value, check_equality)
    return signal.get, signal.set


def create_effect[T](fn: Callable[[], T], call_immediately=True):
    return Effect(fn, call_immediately)


def create_memo[T](fn: Callable[[], T]):
    return Memoized(fn)


def memoized_property[T, I](method: Callable[[I], T]):
    return MemoizedProperty(method)


def memoized_method[T, I](method: Callable[[I], T]):
    return MemoizedMethod(method)


@overload
def batch() -> Batch: ...
@overload
def batch[**P, T](func: Callable[P, T]) -> Callable[P, T]: ...


def batch[**P, T](func: Callable[P, T] | None = None) -> Callable[P, T] | Batch:
    if func is not None:

        @wraps(func)
        def wrapped(*args, **kwargs):
            with Batch():
                return func(*args, **kwargs)

        return wrapped

    return Batch()
