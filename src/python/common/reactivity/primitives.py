from collections.abc import Callable
from typing import Any
from weakref import WeakKeyDictionary, WeakSet


class Subscribable:
    def __init__(self):
        super().__init__()
        self.subscribers = set[BaseComputation]()

    def track(self):
        for computation in _current_computations:
            if computation is not self:
                self.subscribers.add(computation)
                computation.dependencies.add(self)

    def notify(self):
        if _batches:
            _batches[-1].callbacks.extend(self.subscribers)
        else:
            for subscriber in {*self.subscribers}:
                subscriber.trigger()


class BaseComputation:
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

    def __call__(self):
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


class State[T](Signal[T]):
    def __init__(self, initial_value: T = None, check_equality=True):
        super().__init__(initial_value, check_equality)
        self._value = initial_value
        self._check_equality = check_equality
        self.map = WeakKeyDictionary[Any, Signal[T]]()

    def __get__(self, instance, owner):
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


class Derived[T](BaseComputation):
    def __init__(self, fn: Callable[[], T], auto_run=True):
        super().__init__()

        self._fn = fn

        if auto_run:
            self()

    def trigger(self):
        self._before()
        try:
            return self._fn()
        finally:
            self._after()


class Batch:
    def __init__(self):
        self.callbacks: list[BaseComputation] = []

    def flush(self):
        callbacks = set(self.callbacks)
        self.callbacks.clear()
        for computation in callbacks:
            computation.trigger()

    def __enter__(self):
        _batches.append(self)

    def __exit__(self, *_):
        last = _batches.pop()
        assert last is self
        self.flush()


_batches: list[Batch] = []
