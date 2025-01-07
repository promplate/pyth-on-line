from collections.abc import Callable, Mapping, MutableMapping

from .primitives import BaseComputation, Batch, State, Subscribable


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


class MemoizedProperty[T, Self](Subscribable, BaseComputation):
    def __init__(self, method: Callable[[Self], T]):
        super().__init__()
        self.method = method
        self.is_stale = True
        self.cached_value: T
        self._instance: Self | None = None

    def trigger(self):
        if self._instance is not None:
            self._before()
            self.cached_value = self.method(self._instance)
            self._after()
            self.is_stale = False
        elif not self.is_stale:
            del self.cached_value
            self.is_stale = True

    def __get__(self, instance: Self, owner):
        if self.is_stale:
            self._instance = instance
            self.trigger()
            self.notify()
            self._instance = None
        self.track()
        return self.cached_value

    def __delete__(self, instance):
        del self.cached_value
        self.is_stale = True


class Reactive[K, V](Subscribable, MutableMapping[K, V]):
    UNSET: V = object()  # type: ignore

    def __hash__(self):
        return id(self)

    def __init__(self, initial: Mapping | None = None, check_equality=True):
        super().__init__()
        self._states: dict[K, State[V]] = {} if initial is None else {k: State(v, check_equality) for k, v in initial.items()}
        self._check_equality = check_equality

    def __getitem__(self, key: K):
        value = self._states.setdefault(key, State(self.UNSET, self._check_equality)).get()
        if value is self.UNSET:
            raise KeyError(key)
        return value

    def __setitem__(self, key: K, value: V):
        with Batch():
            try:
                self._states[key].set(value)
            except KeyError:
                self._states[key] = State(value, self._check_equality)
                self._states[key].set(value)
            self.notify()

    def __delitem__(self, key: K):
        state = self._states[key]
        if state.get(track=False) is self.UNSET:
            raise KeyError(key)
        with Batch():
            state.set(self.UNSET)
            state.notify()
            self.notify()

    def __iter__(self):
        self.track()
        return iter(self._states)

    def __len__(self):
        self.track()
        return len(self._states)

    def __repr__(self):
        self.track()
        return repr({k: v.get() for k, v in self._states.items()})

    def items(self):
        self.track()
        return ({k: v.get() for k, v in self._states.items()}).items()
