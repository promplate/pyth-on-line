from collections.abc import Callable
from typing import Any
from weakref import WeakSet


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


class State[T](Subscribable):
    def __init__(self, initial_value: T = None):
        super().__init__()
        self._value: T = initial_value

    def get(self):
        self.track()
        return self._value

    def set(self, value: T):
        self._value = value
        self.notify()

    def __get__(self, instance, owner):
        return self.get()

    def __set__(self, instance, value: T):
        self.set(value)


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
