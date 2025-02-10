from collections import defaultdict
from collections.abc import Callable, Mapping, MutableMapping
from functools import partial
from typing import Self, overload
from weakref import WeakKeyDictionary

from .primitives import BaseComputation, Batch, Signal, Subscribable


class Memoized[T](Subscribable, BaseComputation[T]):
    def __init__(self, fn: Callable[[], T]):
        super().__init__()
        self.fn = fn
        self.is_stale = True
        self.cached_value: T

    def recompute(self):
        self._before()
        try:
            self.cached_value = self.fn()
            self.is_stale = False
        finally:
            self._after()

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
    def __init__(self, method: Callable[[I], T]):
        super().__init__()
        self.method = method
        self.map = WeakKeyDictionary[I, Memoized[T]]()

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self: ...
    @overload
    def __get__(self, instance: I, owner: type[I]) -> T: ...

    def __get__(self, instance: I | None, owner):
        if instance is None:
            return self
        if func := self.map.get(instance):
            return func()
        self.map[instance] = func = Memoized(partial(self.method, instance))
        return func()


class MemoizedMethod[T, I]:
    def __init__(self, method: Callable[[I], T]):
        super().__init__()
        self.method = method
        self.map = WeakKeyDictionary[I, Memoized[T]]()

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self: ...
    @overload
    def __get__(self, instance: I, owner: type[I]) -> Memoized[T]: ...

    def __get__(self, instance: I | None, owner):
        if instance is None:
            return self
        if memo := self.map.get(instance):
            return memo
        self.map[instance] = memo = Memoized(partial(self.method, instance))
        return memo


class Reactive[K, V](Subscribable, MutableMapping[K, V]):
    UNSET: V = object()  # type: ignore

    def __hash__(self):
        return id(self)

    def _null(self):
        return Signal(self.UNSET, self._check_equality)

    def __init__(self, initial: Mapping[K, V] | None = None, check_equality=True):
        super().__init__()
        self._signals = defaultdict[K, Signal[V]](self._null) if initial is None else defaultdict(self._null, {k: Signal(v, check_equality) for k, v in initial.items()})
        self._check_equality = check_equality

    def __getitem__(self, key: K):
        value = self._signals[key].get()
        if value is self.UNSET:
            raise KeyError(key)
        return value

    def __setitem__(self, key: K, value: V):
        with Batch():
            self._signals[key].set(value)
            self.notify()

    def __delitem__(self, key: K):
        state = self._signals[key]
        if state.get(track=False) is self.UNSET:
            raise KeyError(key)
        with Batch():
            state.set(self.UNSET)
            self.notify()

    def __iter__(self):
        self.track()
        return iter(self._signals)

    def __len__(self):
        self.track()
        return len(self._signals)

    def __repr__(self):
        self.track()
        return repr({k: v.get() for k, v in self._signals.items()})

    def items(self):
        self.track()
        return ({k: v.get() for k, v in self._signals.items()}).items()
