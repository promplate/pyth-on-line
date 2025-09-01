from collections.abc import Callable
from typing import TYPE_CHECKING, Self, overload
from weakref import WeakKeyDictionary

from .context import Context
from .primitives import BaseComputation, Derived, Subscribable


class Memoized[T](Subscribable, BaseComputation[T]):
    def __init__(self, fn: Callable[[], T], *, context: Context | None = None):
        super().__init__(context=context)
        self.fn = fn
        self.is_stale = True
        self.cached_value: T

    def recompute(self):
        with self._enter():
            self.cached_value = self.fn()
            self.is_stale = False

    def trigger(self):
        self.invalidate()

    def __call__(self):
        self.track()
        if self.is_stale:
            self.recompute()
        return self.cached_value

    def invalidate(self):
        if not self.is_stale:
            del self.cached_value
            self.is_stale = True
            self.notify()


class MemoizedProperty[T, I]:
    def __init__(self, method: Callable[[I], T], *, context: Context | None = None):
        super().__init__()
        self.method = method
        self.map = WeakKeyDictionary[I, Memoized[T]]()
        self.context = context

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self: ...
    @overload
    def __get__(self, instance: I, owner: type[I]) -> T: ...

    def __get__(self, instance: I | None, owner):
        if instance is None:
            return self
        if func := self.map.get(instance):
            return func()
        self.map[instance] = func = Memoized(self.method.__get__(instance, owner), context=self.context)
        return func()


class MemoizedMethod[T, I]:
    def __init__(self, method: Callable[[I], T], *, context: Context | None = None):
        super().__init__()
        self.method = method
        self.map = WeakKeyDictionary[I, Memoized[T]]()
        self.context = context

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self: ...
    @overload
    def __get__(self, instance: I, owner: type[I]) -> Memoized[T]: ...

    def __get__(self, instance: I | None, owner):
        if instance is None:
            return self
        if memo := self.map.get(instance):
            return memo
        self.map[instance] = memo = Memoized(self.method.__get__(instance, owner), context=self.context)
        return memo


class DerivedProperty[T, I]:
    def __init__(self, method: Callable[[I], T], *, context: Context | None = None):
        super().__init__()
        self.method = method
        self.map = WeakKeyDictionary[I, Derived[T]]()
        self.context = context

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self: ...
    @overload
    def __get__(self, instance: I, owner: type[I]) -> T: ...

    def __get__(self, instance: I | None, owner):
        if instance is None:
            return self
        if func := self.map.get(instance):
            return func()
        self.map[instance] = func = Derived(self.method.__get__(instance, owner), context=self.context)
        return func()


class DerivedMethod[T, I]:
    def __init__(self, method: Callable[[I], T], check_equality=True, *, context: Context | None = None):
        super().__init__()
        self.method = method
        self.check_equality = check_equality
        self.map = WeakKeyDictionary[I, Derived[T]]()
        self.context = context

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self: ...
    @overload
    def __get__(self, instance: I, owner: type[I]) -> Derived[T]: ...

    def __get__(self, instance: I | None, owner):
        if instance is None:
            return self
        if func := self.map.get(instance):
            return func

        self.map[instance] = func = Derived(self.method.__get__(instance, owner), self.check_equality, context=self.context)
        return func


if TYPE_CHECKING:
    from typing_extensions import deprecated

    from .collections import ReactiveMapping

    @deprecated("Use `ReactiveMapping` instead")
    class Reactive[K, V](ReactiveMapping[K, V]): ...

else:
    from .collections import ReactiveMapping as Reactive  # noqa: F401
