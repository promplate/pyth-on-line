from collections.abc import Callable, Iterable
from typing import Any, Self, overload
from weakref import WeakKeyDictionary, WeakSet


class Subscribable:
    def __init__(self):
        super().__init__()
        self.subscribers = set[BaseComputation]()

    def track(self):
        if not _current_computations:
            return
        last = _current_computations[-1]
        if last is not self:
            self.subscribers.add(last)
            last.dependencies.add(self)

    def notify(self):
        if _batches:
            schedule_callbacks(self.subscribers)
        else:
            with Batch(force_flush=False):
                schedule_callbacks(self.subscribers)


class BaseComputation[T]:
    def __init__(self):
        super().__init__()
        self.dependencies = WeakSet[Subscribable]()

    def dispose(self):
        for dep in self.dependencies:
            dep.subscribers.remove(self)
        self.dependencies.clear()

    def _before(self):
        self.dispose()
        _current_computations.append(self)

    def _after(self):
        last = _current_computations.pop()
        assert last is self  # sanity check

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.dispose()

    def trigger(self) -> Any: ...

    def __call__(self) -> T:
        return self.trigger()


_current_computations: list[BaseComputation] = []


class Signal[T](Subscribable):
    def __init__(self, initial_value: T = None, check_equality=True):
        super().__init__()
        self._value: T = initial_value
        self._check_equality = check_equality

    def get(self, track=True):
        if track:
            self.track()
        return self._value

    def set(self, value: T):
        if not self._check_equality or self._value != value:
            self._value = value
            self.notify()
            return True
        return False


class State[T](Signal[T]):
    def __init__(self, initial_value: T = None, check_equality=True):
        super().__init__(initial_value, check_equality)
        self._value = initial_value
        self._check_equality = check_equality
        self.map = WeakKeyDictionary[Any, Signal[T]]()

    @overload
    def __get__(self, instance: None, owner: type) -> Self: ...
    @overload
    def __get__(self, instance: Any, owner: type) -> T: ...

    def __get__(self, instance, owner):
        if instance is None:
            return self
        try:
            return self.map[instance].get()
        except KeyError:
            self.map[instance] = state = Signal(self._value, self._check_equality)
            return state.get()

    def __set__(self, instance, value: T):
        try:
            state = self.map[instance]
        except KeyError:
            self.map[instance] = state = Signal(self._value, self._check_equality)
        state.set(value)


class Effect[T](BaseComputation[T]):
    def __init__(self, fn: Callable[[], T], call_immediately=True):
        super().__init__()

        self._fn = fn

        if call_immediately:
            self()

    def trigger(self):
        self._before()
        try:
            return self._fn()
        finally:
            self._after()


class Batch:
    def __init__(self, force_flush=True):
        self.callbacks = set[BaseComputation]()
        self.force_flush = force_flush

    def flush(self):
        triggered = set()
        while self.callbacks:
            callbacks = self.callbacks - triggered
            self.callbacks.clear()
            for computation in callbacks:
                if computation in self.callbacks:
                    continue  # skip if re-added during callback
                computation.trigger()
                triggered.add(computation)

    def __enter__(self):
        _batches.append(self)

    def __exit__(self, *_):
        if self.force_flush or len(_batches) == 1:
            try:
                self.flush()
            finally:
                last = _batches.pop()
        else:
            last = _batches.pop()
            schedule_callbacks(self.callbacks)
        assert last is self


_batches: list[Batch] = []


def schedule_callbacks(callbacks: Iterable[BaseComputation]):
    _batches[-1].callbacks.update(callbacks)


class BaseDerived[T](Subscribable, BaseComputation[T]):
    def __init__(self):
        super().__init__()
        self.dirty = True

    def _sync_dirty_deps(self):
        for dep in self.dependencies:
            if isinstance(dep, BaseDerived) and dep.dirty:
                dep()


class Derived[T](BaseDerived[T]):
    UNSET: T = object()  # type: ignore

    def __init__(self, fn: Callable[[], T], check_equality=True):
        super().__init__()
        self.fn = fn
        self._check_equality = check_equality
        self._value = self.UNSET

    def recompute(self):
        self._before()
        try:
            value = self.fn()
            self.dirty = False
            if self._check_equality:
                if value == self._value:
                    return
                elif self._value is self.UNSET:  # do not notify on first set
                    self._value = value
                    return
            self._value = value
            self.notify()
        finally:
            self._after()

    def __call__(self):
        self.track()
        self._sync_dirty_deps()
        if self.dirty:
            self.recompute()

        return self._value

    def trigger(self):
        self.dirty = True
        if _pulled(self):
            self()

    def invalidate(self):
        self.trigger()


def _pulled(sub: Subscribable):
    visited = set()
    to_visit: set[Subscribable] = {sub}
    while to_visit:
        visited.add(current := to_visit.pop())
        for s in current.subscribers:
            if not isinstance(s, BaseDerived):
                return True
            if s not in visited:
                to_visit.add(s)
    return False
