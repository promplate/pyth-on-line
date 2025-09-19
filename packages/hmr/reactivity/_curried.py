from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, overload

from .context import Context


def signal[T](initial_value: T = None, /, check_equality=True, *, context: Context | None = None) -> Signal[T]:
    return Signal(initial_value, check_equality, context=context)


def state[T](initial_value: T = None, /, check_equality=True, *, context: Context | None = None) -> State[T]:
    return State(initial_value, check_equality, context=context)


__: Any = object()  # sentinel


@overload
def effect[T](fn: Callable[[], T], /, call_immediately=True, *, context: Context | None = None) -> Effect[T]: ...
@overload
def effect[T](*, call_immediately=True, context: Context | None = None) -> Callable[[Callable[[], T]], Effect[T]]: ...


def effect[T](fn: Callable[[], T] = __, /, call_immediately=True, *, context: Context | None = None):  # type: ignore
    if fn is __:
        return lambda fn: Effect(fn, call_immediately, context=context)
    return Effect(fn, call_immediately, context=context)


@overload
def derived[T](fn: Callable[[], T], /, check_equality=True, *, context: Context | None = None) -> Derived[T]: ...
@overload
def derived[T](*, check_equality=True, context: Context | None = None) -> Callable[[Callable[[], T]], Derived[T]]: ...


def derived[T](fn: Callable[[], T] = __, /, check_equality=True, *, context: Context | None = None):  # type: ignore
    if fn is __:
        return lambda fn: Derived(fn, check_equality, context=context)
    return Derived(fn, check_equality, context=context)


@overload
def derived_property[T, I](method: Callable[[I], T], /, check_equality=True, *, context: Context | None = None) -> DerivedProperty[T, I]: ...
@overload
def derived_property[T, I](*, check_equality=True, context: Context | None = None) -> Callable[[Callable[[I], T]], DerivedProperty[T, I]]: ...


def derived_property[T, I](method: Callable[[I], T] = __, /, check_equality=True, *, context: Context | None = None):  # type: ignore
    if method is __:
        return lambda method: DerivedProperty(method, check_equality, context=context)
    return DerivedProperty(method, check_equality, context=context)


@overload
def derived_method[T, I](method: Callable[[I], T], /, check_equality=True, *, context: Context | None = None) -> DerivedMethod[T, I]: ...
@overload
def derived_method[T, I](*, check_equality=True, context: Context | None = None) -> Callable[[Callable[[I], T]], DerivedMethod[T, I]]: ...


def derived_method[T, I](method: Callable[[I], T] = __, /, check_equality=True, *, context: Context | None = None):  # type: ignore
    if method is __:
        return lambda method: DerivedMethod(method, check_equality, context=context)
    return DerivedMethod(method, check_equality, context=context)


@overload
def memoized[T](fn: Callable[[], T], /, *, context: Context | None = None) -> Memoized[T]: ...
@overload
def memoized[T](*, context: Context | None = None) -> Callable[[Callable[[], T]], Memoized[T]]: ...


def memoized[T](fn: Callable[[], T] = __, /, *, context: Context | None = None):  # type: ignore
    if fn is __:
        return lambda fn: Memoized(fn, context=context)
    return Memoized(fn, context=context)


@overload
def memoized_property[T, I](method: Callable[[I], T], /, *, context: Context | None = None) -> MemoizedProperty[T, I]: ...
@overload
def memoized_property[T, I](*, context: Context | None = None) -> Callable[[Callable[[I], T]], MemoizedProperty[T, I]]: ...


def memoized_property[T, I](method: Callable[[I], T] = __, /, *, context: Context | None = None):  # type: ignore
    if method is __:
        return lambda method: MemoizedProperty(method, context=context)
    return MemoizedProperty(method, context=context)


@overload
def memoized_method[T, I](method: Callable[[I], T], /, *, context: Context | None = None) -> MemoizedMethod[T, I]: ...
@overload
def memoized_method[T, I](*, context: Context | None = None) -> Callable[[Callable[[I], T]], MemoizedMethod[T, I]]: ...


def memoized_method[T, I](method: Callable[[I], T] = __, /, *, context: Context | None = None):  # type: ignore
    if method is __:
        return lambda method: MemoizedMethod(method, context=context)
    return MemoizedMethod(method, context=context)


@overload
def async_effect[T](fn: Callable[[], Awaitable[T]], /, call_immediately=True, *, context: Context | None = None, task_factory: TaskFactory | None = None) -> AsyncEffect[T]: ...
@overload
def async_effect[T](*, call_immediately=True, context: Context | None = None, task_factory: TaskFactory | None = None) -> Callable[[Callable[[], Awaitable[T]]], AsyncEffect[T]]: ...


def async_effect[T](fn: Callable[[], Awaitable[T]] = __, /, call_immediately=True, *, context: Context | None = None, task_factory: TaskFactory | None = None):  # type: ignore
    if fn is __:
        return lambda fn: AsyncEffect(fn, call_immediately, context=context, task_factory=task_factory or default_task_factory)
    return AsyncEffect(fn, call_immediately, context=context, task_factory=task_factory or default_task_factory)


@overload
def async_derived[T](fn: Callable[[], Awaitable[T]], /, check_equality=True, *, context: Context | None = None, task_factory: TaskFactory | None = None) -> AsyncDerived[T]: ...
@overload
def async_derived[T](*, check_equality=True, context: Context | None = None, task_factory: TaskFactory | None = None) -> Callable[[Callable[[], Awaitable[T]]], AsyncDerived[T]]: ...


def async_derived[T](fn: Callable[[], Awaitable[T]] = __, /, check_equality=True, *, context: Context | None = None, task_factory: TaskFactory | None = None):  # type: ignore
    if fn is __:
        return lambda fn: AsyncDerived(fn, check_equality, context=context, task_factory=task_factory or default_task_factory)
    return AsyncDerived(fn, check_equality, context=context, task_factory=task_factory or default_task_factory)


@overload
def batch(*, context: Context | None = None) -> Batch: ...
@overload
def batch[**P, T](func: Callable[P, T], /, context: Context | None = None) -> Callable[P, T]: ...


def batch[**P, T](func: Callable[P, T] = __, /, context: Context | None = None) -> Callable[P, T] | Batch:
    if func is __:
        return Batch(context=context)

    @wraps(func)
    def wrapped(*args, **kwargs):
        with Batch(context=context):
            return func(*args, **kwargs)

    return wrapped


from .async_primitives import AsyncDerived, AsyncEffect, TaskFactory, default_task_factory
from .helpers import DerivedMethod, DerivedProperty, Memoized, MemoizedMethod, MemoizedProperty
from .primitives import Batch, Derived, Effect, Signal, State
