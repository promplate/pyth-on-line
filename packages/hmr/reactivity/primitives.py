from collections.abc import Callable
from typing import Any, Self, overload
from weakref import WeakKeyDictionary, WeakSet

from .context import Context, default_context


def _equal(a, b):
    if a is b:
        return True
    comparison_result: Any = False
    for i in range(3):  # pandas DataFrame's .all() returns a Series, which is still incompatible :(
        try:
            if i == 0:
                comparison_result = a == b
            if comparison_result:
                return True
        except ValueError as e:
            if ".all()" in str(e) and hasattr(comparison_result, "all"):  # array-like instances
                comparison_result = comparison_result.all()
            else:
                return False
    return False


class Subscribable:
    def __init__(self, *, context: Context | None = None):
        super().__init__()
        self.subscribers = set[BaseComputation]()
        self.context = context or default_context

    def track(self):
        if not self.context.current_computations:
            return
        last = self.context.current_computations[-1]
        if last is not self:
            self.subscribers.add(last)
            last.dependencies.add(self)

    def notify(self):
        if self.context.batches:
            self.context.schedule_callbacks(self.subscribers)
        else:
            with Batch(force_flush=False, context=self.context):
                self.context.schedule_callbacks(self.subscribers)


class BaseComputation[T]:
    def __init__(self, *, context: Context | None = None):
        super().__init__()
        self.dependencies = WeakSet[Subscribable]()
        self.context = context or default_context

    def dispose(self):
        for dep in self.dependencies:
            dep.subscribers.remove(self)
        self.dependencies.clear()

    def _enter(self):
        return self.context.enter(self)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.dispose()

    def trigger(self) -> Any: ...

    def __call__(self) -> T:
        return self.trigger()


class Signal[T](Subscribable):
    def __init__(self, initial_value: T = None, check_equality=True, *, context: Context | None = None):
        super().__init__(context=context)
        self._value: T = initial_value
        self._check_equality = check_equality

    def get(self, track=True):
        if track:
            self.track()
        return self._value

    def set(self, value: T):
        if not self._check_equality or not _equal(self._value, value):
            self._value = value
            self.notify()
            return True
        return False


class State[T](Signal[T]):
    def __init__(self, initial_value: T = None, check_equality=True, *, context: Context | None = None):
        super().__init__(initial_value, check_equality, context=context)
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
            self.map[instance] = state = Signal(self._value, self._check_equality, context=self.context)
            return state.get()

    def __set__(self, instance, value: T):
        try:
            state = self.map[instance]
        except KeyError:
            self.map[instance] = state = Signal(self._value, self._check_equality, context=self.context)
        state.set(value)


class Effect[T](BaseComputation[T]):
    def __init__(self, fn: Callable[[], T], call_immediately=True, *, context: Context | None = None):
        super().__init__(context=context)

        self._fn = fn

        if call_immediately:
            self()

    def trigger(self):
        with self._enter():
            return self._fn()


class Batch:
    def __init__(self, force_flush=True, *, context: Context | None = None):
        self.callbacks = set[BaseComputation]()
        self.force_flush = force_flush
        self.context = context or default_context

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
        self.context.batches.append(self)

    def __exit__(self, *_):
        if self.force_flush or len(self.context.batches) == 1:
            try:
                self.flush()
            finally:
                last = self.context.batches.pop()
        else:
            last = self.context.batches.pop()
            self.context.schedule_callbacks(self.callbacks)
        assert last is self


class BaseDerived[T](Subscribable, BaseComputation[T]):
    def __init__(self, *, context: Context | None = None):
        super().__init__(context=context)
        self.dirty = True

    def _sync_dirty_deps(self):
        for dep in self.dependencies:
            if isinstance(dep, BaseDerived) and dep.dirty:
                dep()


class Derived[T](BaseDerived[T]):
    UNSET: T = object()  # type: ignore

    def __init__(self, fn: Callable[[], T], check_equality=True, *, context: Context | None = None):
        super().__init__(context=context)
        self.fn = fn
        self._check_equality = check_equality
        self._value = self.UNSET

    def recompute(self):
        with self._enter():
            value = self.fn()
            self.dirty = False
            if self._check_equality:
                if _equal(value, self._value):
                    return
                elif self._value is self.UNSET:  # do not notify on first set
                    self._value = value
                    return
            self._value = value
            self.notify()

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
