from collections.abc import Callable
from typing import Any, Self, overload
from weakref import WeakKeyDictionary, WeakSet

from .context import Context, default_context


def _equal(a, b):
    """
    Compares two values for equality, handling special cases for array-like objects.
    
    Attempts to compare `a` and `b` up to three times, using `.all()` if the initial comparison raises a ValueError and the result supports it. Returns True if the values are considered equal, otherwise False.
    """
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
        """
        Initializes a Subscribable object with an empty set of subscribers and an optional reactive context.
        
        Args:
            context: The reactive context to associate with this Subscribable. If not provided, the default context is used.
        """
        super().__init__()
        self.subscribers = set[BaseComputation]()
        self.context = context or default_context

    def track(self):
        """
        Registers the current computation as a subscriber to this object if tracking is active.
        
        If there is an active computation in the context, adds it as a subscriber and establishes a dependency, ensuring that updates to this object will notify the computation.
        """
        if not self.context.current_computations:
            return
        last = self.context.current_computations[-1]
        if last is not self:
            with self.context.untrack():
                self.subscribers.add(last)
                last.dependencies.add(self)

    def notify(self):
        """
        Notifies all subscribers of this object about a change.
        
        If batching is active in the current context, schedules subscriber callbacks for execution. Otherwise, creates a new batch to schedule the callbacks, ensuring updates are processed efficiently.
        """
        if self.context.batches:
            self.context.schedule_callbacks(self.subscribers)
        else:
            with Batch(force_flush=False, context=self.context):
                self.context.schedule_callbacks(self.subscribers)


class BaseComputation[T]:
    def __init__(self, *, context: Context | None = None):
        """
        Initializes a reactive computation with an optional context.
        
        Args:
            context: The reactive context to associate with this computation. If not provided, the default context is used.
        """
        super().__init__()
        self.dependencies = WeakSet[Subscribable]()
        self.context = context or default_context

    def dispose(self):
        """
        Removes this computation from all its dependencies and clears its dependency set.
        """
        for dep in self.dependencies:
            dep.subscribers.remove(self)
        self.dependencies.clear()

    def _enter(self):
        """
        Enters this computation into the current reactive context for dependency tracking.
        
        Returns:
            The result of entering this computation in the context, as provided by the context's `enter` method.
        """
        return self.context.enter(self)

    def __enter__(self):
        """
        Enters the context manager and returns the current instance.
        """
        return self

    def __exit__(self, *_):
        """
        Cleans up resources and dependencies when exiting the computation's context.
        """
        self.dispose()

    def trigger(self) -> Any: """
Executes the effect's function within the reactive computation context and returns its result.
"""
...

    def __call__(self) -> T:
        """
        Invokes the computation by triggering its execution and returning the result.
        """
        return self.trigger()


class Signal[T](Subscribable):
    def __init__(self, initial_value: T = None, check_equality=True, *, context: Context | None = None):
        """
        Initializes a reactive signal with an optional initial value and equality checking.
        
        Args:
            initial_value: The starting value for the signal.
            check_equality: If True, updates only trigger notifications when the value changes.
            context: Optional reactive context to associate with this signal.
        """
        super().__init__(context=context)
        self._value: T = initial_value
        self._check_equality = check_equality

    def get(self, track=True):
        """
        Returns the current value of the signal, optionally registering a dependency.
        
        Args:
            track: If True, registers the current computation as a dependent of this signal.
        
        Returns:
            The current stored value.
        """
        if track:
            self.track()
        return self._value

    def set(self, value: T):
        """
        Sets the signal's value and notifies subscribers if the value has changed.
        
        Args:
            value: The new value to assign to the signal.
        
        Returns:
            True if the value was updated and subscribers were notified, False if the value was unchanged.
        """
        if not self._check_equality or not _equal(self._value, value):
            self._value = value
            self.notify()
            return True
        return False


class State[T](Signal[T]):
    def __init__(self, initial_value: T = None, check_equality=True, *, context: Context | None = None):
        """
        Initializes a State descriptor for managing per-instance reactive state.
        
        Args:
            initial_value: The default value for new instances.
            check_equality: If True, updates only trigger notifications when the value changes.
            context: Optional reactive context to associate with this state.
        """
        super().__init__(initial_value, check_equality, context=context)
        self._value = initial_value
        self._check_equality = check_equality
        self.map = WeakKeyDictionary[Any, Signal[T]]()

    @overload
    def __get__(self, instance: None, owner: type) -> Self: """
Returns the descriptor itself when accessed on the class rather than an instance.
"""
...
    @overload
    def __get__(self, instance: Any, owner: type) -> T: """
Retrieves the reactive state value for the given instance.

If accessed on the class, returns the descriptor itself. Otherwise, returns the value associated with the instance, creating a new reactive signal if necessary.
"""
...

    def __get__(self, instance, owner):
        """
        Retrieves the reactive state value for the given instance.
        
        If accessed on the class, returns the descriptor itself. If accessed on an instance, returns the current value, creating a new reactive signal for the instance if necessary.
        """
        if instance is None:
            return self
        try:
            return self.map[instance].get()
        except KeyError:
            self.map[instance] = state = Signal(self._value, self._check_equality, context=self.context)
            return state.get()

    def __set__(self, instance, value: T):
        """
        Sets the reactive state value for the given instance.
        
        If the instance does not yet have an associated Signal, creates one before setting the value.
        """
        try:
            state = self.map[instance]
        except KeyError:
            self.map[instance] = state = Signal(self._value, self._check_equality, context=self.context)
        state.set(value)


class Effect[T](BaseComputation[T]):
    def __init__(self, fn: Callable[[], T], call_immediately=True, *, context: Context | None = None):
        """
        Initializes an Effect that runs a reactive function and tracks its dependencies.
        
        Args:
            fn: The function to execute reactively.
            call_immediately: If True, the function is executed immediately upon creation.
            context: Optional reactive context to use for dependency tracking.
        """
        super().__init__(context=context)

        self._fn = fn

        if call_immediately:
            self()

    def trigger(self):
        """
        Executes the effect's function within the reactive computation context and returns its result.
        """
        with self._enter():
            return self._fn()


class Batch:
    def __init__(self, force_flush=True, *, context: Context | None = None):
        """
        Initializes a new batch for grouping reactive updates.
        
        Args:
            force_flush: If True, flushes all scheduled callbacks when the batch exits.
            context: Optional reactive context to use; defaults to the global context.
        """
        self.callbacks = set[BaseComputation]()
        self.force_flush = force_flush
        self.context = context or default_context

    def flush(self):
        """
        Executes all scheduled reactive computations in the batch.
        
        Ensures each computation is triggered only once, even if re-added during execution.
        """
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
        """
        Enters the batch context, adding this batch to the context's batch stack.
        """
        self.context.batches.append(self)

    def __exit__(self, *_):
        """
        Exits the batch context, flushing or scheduling callbacks as appropriate.
        
        If this is the last batch or force flushing is enabled, all scheduled callbacks are executed immediately. Otherwise, callbacks are scheduled for later execution. Ensures the batch is properly removed from the context stack.
        """
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
        """
        Initializes a derived reactive computation and marks it as dirty.
        
        Args:
            context: Optional reactive context to associate with this computation.
        """
        super().__init__(context=context)
        self.dirty = True

    def _sync_dirty_deps(self):
        """
        Recursively synchronizes and recomputes dirty derived dependencies.
        
        Triggers any dependent `BaseDerived` computations that are marked as dirty to ensure their values are up to date.
        """
        for dep in self.dependencies:
            if isinstance(dep, BaseDerived) and dep.dirty:
                dep()


class Derived[T](BaseDerived[T]):
    UNSET: T = object()  # type: ignore

    def __init__(self, fn: Callable[[], T], check_equality=True, *, context: Context | None = None):
        """
        Initializes a derived reactive value with a computation function.
        
        Args:
            fn: A callable that computes the derived value.
            check_equality: If True, notifies subscribers only when the computed value changes.
            context: Optional reactive context to use for dependency tracking.
        """
        super().__init__(context=context)
        self.fn = fn
        self._check_equality = check_equality
        self._value = self.UNSET

    def recompute(self):
        """
        Recomputes the derived value and notifies subscribers if it has changed.
        
        Runs the computation function within the reactive context, updates the cached value, and marks the derived value as clean. Subscribers are notified only if the value has changed, except on the initial set.
        """
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
        """
        Returns the current value of the derived computation, recomputing if dependencies have changed.
        
        Tracks dependencies, synchronizes any dirty dependent computations, and triggers recomputation if needed before returning the cached value.
        """
        self.track()
        self._sync_dirty_deps()
        if self.dirty:
            self.recompute()

        return self._value

    def trigger(self):
        """
        Marks the derived computation as dirty and triggers recomputation if it is actively observed.
        
        If the derived value is currently being used by an active consumer, recomputes its value immediately.
        """
        self.dirty = True
        if _pulled(self):
            self()

    def invalidate(self):
        """
        Marks the derived computation as dirty and triggers recomputation if actively used.
        
        This method is an alias for `trigger()`.
        """
        self.trigger()


def _pulled(sub: Subscribable):
    """
    Determines whether a Subscribable is actively observed by any non-derived subscriber.
    
    Traverses the subscriber graph starting from the given Subscribable. Returns True if any subscriber is not a BaseDerived instance, indicating the value is being "pulled" by an active consumer; otherwise, returns False.
    """
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
