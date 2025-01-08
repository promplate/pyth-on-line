from collections.abc import Callable, Mapping, MutableMapping
from functools import partial
from weakref import WeakKeyDictionary

from .primitives import BaseComputation, Batch, Signal, Subscribable


class Memoized[T](Subscribable, BaseComputation):
    def __init__(self, fn: Callable[[], T]):
        super().__init__()
        self.fn = fn
        self.is_stale = True
        self.cached_value: T
        self._recompute = False

    def trigger(self):
        if self._recompute:
            self._before()
            self.cached_value = self.fn()
            self._after()
            self.is_stale = False
        elif not self.is_stale:
            del self.cached_value
            self.is_stale = True
        self.track()

    def __call__(self):
        if self.is_stale:
            self._recompute = True
            self.trigger()
            self._recompute = False
        return self.cached_value

    def invalidate(self):
        del self.cached_value
        self.is_stale = True


class MemoizedProperty[T, Self]:
    def __init__(self, method: Callable[[Self], T]):
        super().__init__()
        self.method = method
        self.map = WeakKeyDictionary[Self, Memoized]()

    def __get__(self, instance, owner):
        if func := self.map.get(instance):
            return func()
        self.map[instance] = func = Memoized(partial(self.method, instance))
        return func()


class MemoizedMethod[T, Self]:
    def __init__(self, method: Callable[[Self], T]):
        super().__init__()
        self.method = method

    def __get__(self, instance, owner):
        return Memoized(partial(self.method, instance))


class Reactive[K, V](Subscribable, MutableMapping[K, V]):
    UNSET: V = object()  # type: ignore

    def __hash__(self):
        return id(self)

    def __init__(self, initial: Mapping | None = None, check_equality=True):
        super().__init__()
        self._signals: dict[K, Signal[V]] = {} if initial is None else {k: Signal(v, check_equality) for k, v in initial.items()}
        self._check_equality = check_equality

    def __getitem__(self, key: K):
        value = self._signals.setdefault(key, Signal(self.UNSET, self._check_equality)).get()
        if value is self.UNSET:
            raise KeyError(key)
        return value

    def __setitem__(self, key: K, value: V):
        with Batch():
            try:
                self._signals[key].set(value)
            except KeyError:
                self._signals[key] = Signal(value, self._check_equality)
                self._signals[key].set(value)
            self.notify()

    def __delitem__(self, key: K):
        state = self._signals[key]
        if state.get(track=False) is self.UNSET:
            raise KeyError(key)
        with Batch():
            state.set(self.UNSET)
            state.notify()
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
