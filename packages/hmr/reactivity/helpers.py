from collections import defaultdict
from collections.abc import Callable, Mapping, MutableMapping
from typing import Self, overload
from weakref import WeakKeyDictionary

from .context import Context
from .primitives import BaseComputation, Batch, Derived, Signal, Subscribable


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


class Reactive[K, V](Subscribable, MutableMapping[K, V]):
    UNSET: V = object()  # type: ignore

    def __hash__(self):
        return id(self)

    def _null(self):
        return Signal(self.UNSET, self._check_equality)

    def __init__(self, initial: Mapping[K, V] | None = None, check_equality=True, *, context: Context | None = None):
        super().__init__(context=context)
        self._signals = defaultdict[K, Signal[V]](self._null) if initial is None else defaultdict(self._null, {k: Signal(v, check_equality, context=context) for k, v in initial.items()})
        self._check_equality = check_equality

    def __getitem__(self, key: K):
        value = self._signals[key].get()
        if value is self.UNSET:
            raise KeyError(key)
        return value

    def __setitem__(self, key: K, value: V):
        with Batch(force_flush=False, context=self.context):
            if self._signals[key].set(value):
                self.notify()

    def __delitem__(self, key: K):
        state = self._signals[key]
        if state.get(track=False) is self.UNSET:
            raise KeyError(key)
        with Batch(force_flush=False, context=self.context):
            state.set(self.UNSET)
            self.notify()

    def __iter__(self):
        self.track()
        unset = self.UNSET
        return (key for key, signal in self._signals.items() if signal.get(track=False) is not unset)

    def __len__(self):
        self.track()
        unset = self.UNSET
        return sum(signal.get(track=False) is not unset for signal in self._signals.values())

    def __repr__(self):
        self.track()
        unset = self.UNSET
        return repr({k: value for k, v in self._signals.items() if (value := v.get()) is not unset})

    def items(self):
        self.track()
        return ({k: v.get() for k, v in self._signals.items()}).items()


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
