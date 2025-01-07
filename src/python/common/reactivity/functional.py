from collections.abc import Callable
from functools import wraps
from typing import overload

from .helpers import Memoized, MemoizedProperty
from .primitives import Batch, Derived, State


def create_signal[T](initial_value: T = None, check_equality=True) -> tuple[Callable[[], T], Callable[[T], None]]:
    signal = State(initial_value, check_equality)
    return signal.get, signal.set


def create_effect[T](fn: Callable[[], T], auto_run=True):
    return Derived(fn, auto_run)


def create_memo[T](fn: Callable[[], T]):
    return Memoized(fn)


def memoized_property[T, Self](method: Callable[[Self], T]):
    return MemoizedProperty(method)


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
