from collections.abc import Callable
from typing import TYPE_CHECKING, Self, overload

from .context import Context
from .primitives import BaseComputation, Derived, DescriptorMixin, Subscribable


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


def _not_implemented(self, instance, *_):
    raise NotImplementedError(f"{type(instance).__name__}.{self.name} is read-only")  # todo: support optimistic updates


class MemoizedProperty[T, I](DescriptorMixin[Memoized[T]]):
    def __init__(self, method: Callable[[I], T], *, context: Context | None = None):
        super().__init__()
        self.method = method
        self.context = context

    def _new(self, instance):
        return Memoized(self.method.__get__(instance), context=self.context)

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self: ...
    @overload
    def __get__(self, instance: I, owner: type[I]) -> T: ...

    def __get__(self, instance: I | None, owner):
        if instance is None:
            return self
        return self.find(instance)()

    __delete__ = __set__ = _not_implemented


class MemoizedMethod[T, I](DescriptorMixin[Memoized[T]]):
    def __init__(self, method: Callable[[I], T], *, context: Context | None = None):
        super().__init__()
        self.method = method
        self.context = context

    def _new(self, instance):
        return Memoized(self.method.__get__(instance), context=self.context)

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self: ...
    @overload
    def __get__(self, instance: I, owner: type[I]) -> Memoized[T]: ...

    def __get__(self, instance: I | None, owner):
        if instance is None:
            return self
        return self.find(instance)

    __delete__ = __set__ = _not_implemented


class DerivedProperty[T, I](DescriptorMixin[Derived[T]]):
    def __init__(self, method: Callable[[I], T], check_equality=True, *, context: Context | None = None):
        super().__init__()
        self.method = method
        self.check_equality = check_equality
        self.context = context

    def _new(self, instance):
        return Derived(self.method.__get__(instance), self.check_equality, context=self.context)

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self: ...
    @overload
    def __get__(self, instance: I, owner: type[I]) -> T: ...

    def __get__(self, instance: I | None, owner):
        if instance is None:
            return self
        return self.find(instance)()

    __delete__ = __set__ = _not_implemented


class DerivedMethod[T, I](DescriptorMixin[Derived[T]]):
    def __init__(self, method: Callable[[I], T], check_equality=True, *, context: Context | None = None):
        super().__init__()
        self.method = method
        self.check_equality = check_equality
        self.context = context

    def _new(self, instance):
        return Derived(self.method.__get__(instance), self.check_equality, context=self.context)

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self: ...
    @overload
    def __get__(self, instance: I, owner: type[I]) -> Derived[T]: ...

    def __get__(self, instance: I | None, owner):
        if instance is None:
            return self
        return self.find(instance)

    __delete__ = __set__ = _not_implemented


if TYPE_CHECKING:
    from typing_extensions import deprecated  # noqa: UP035

    from .collections import ReactiveMapping

    @deprecated("Use `ReactiveMapping` instead")
    class Reactive[K, V](ReactiveMapping[K, V]): ...

else:
    from .collections import ReactiveMapping as Reactive  # noqa: F401
