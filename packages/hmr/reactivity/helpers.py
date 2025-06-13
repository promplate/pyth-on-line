from collections import defaultdict
from collections.abc import Callable, Mapping, MutableMapping
from typing import Self, overload
from weakref import WeakKeyDictionary

from .context import Context
from .primitives import BaseComputation, Batch, Derived, Signal, Subscribable


class Memoized[T](Subscribable, BaseComputation[T]):
    def __init__(self, fn: Callable[[], T], *, context: Context | None = None):
        """
        Initializes a Memoized computation with a zero-argument function.

        Args:
            fn: The function whose result will be cached and recomputed when invalidated.
            context: Optional reactive context for dependency tracking.
        """
        super().__init__(context=context)
        self.fn = fn
        self.is_stale = True
        self.cached_value: T

    def recompute(self):
        """
        Recomputes and updates the cached value by executing the memoized function within the current context.

        Resets the stale flag after updating the cached value.
        """
        with self._enter():
            self.cached_value = self.fn()
            self.is_stale = False

    def trigger(self):
        """
        Marks the cached value as stale and notifies subscribers of the change.
        """
        self.invalidate()

    def __call__(self):
        """
        Returns the cached value, recomputing it if the memoized function is marked as stale.

        Tracks dependencies for reactive updates. If the cached value is outdated, the underlying function is re-executed to refresh the value before returning it.
        """
        self.track()
        if self.is_stale:
            self.recompute()
        return self.cached_value

    def invalidate(self):
        """
        Marks the cached value as stale and notifies subscribers.

        Deletes the cached value if it is not already stale, sets the stale flag, and triggers subscriber notifications.
        """
        if not self.is_stale:
            del self.cached_value
            self.is_stale = True
            self.notify()


class MemoizedProperty[T, I]:
    def __init__(self, method: Callable[[I], T], *, context: Context | None = None):
        """
        Initializes the memoized property descriptor with the target method and optional context.

        Args:
            method: The instance method to be memoized as a property.
            context: Optional context for reactive computations.
        """
        super().__init__()
        self.method = method
        self.map = WeakKeyDictionary[I, Memoized[T]]()
        self.context = context

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self:
        """
        Returns the descriptor itself when accessed on the class rather than an instance.
        """

    @overload
    def __get__(self, instance: I, owner: type[I]) -> T:
        """
        Returns the memoized value for the given instance, computing and caching it if necessary.

        If accessed on the class, returns the descriptor itself.
        """

    def __get__(self, instance: I | None, owner):
        """
        Returns the memoized value for the instance, creating and caching a Memoized computation if needed.

        If accessed on the class, returns the descriptor itself.
        """
        if instance is None:
            return self
        if func := self.map.get(instance):
            return func()
        self.map[instance] = func = Memoized(self.method.__get__(instance, owner), context=self.context)
        return func()


class MemoizedMethod[T, I]:
    def __init__(self, method: Callable[[I], T], *, context: Context | None = None):
        """
        Initializes the memoized property descriptor with the target method and optional context.

        Args:
            method: The instance method to be memoized as a property.
            context: Optional context for reactive computations.
        """
        super().__init__()
        self.method = method
        self.map = WeakKeyDictionary[I, Memoized[T]]()
        self.context = context

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self:
        """
        Returns the descriptor itself when accessed on the class rather than an instance.
        """

    @overload
    def __get__(self, instance: I, owner: type[I]) -> Memoized[T]:
        """
        Returns the Memoized computation for the given instance, creating it if necessary.

        If accessed on the class, returns the descriptor itself.
        """

    def __get__(self, instance: I | None, owner):
        """
        Returns the Memoized object for the given instance, creating and caching it if necessary.

        If accessed on the class, returns the descriptor itself.
        """
        if instance is None:
            return self
        if memo := self.map.get(instance):
            return memo
        self.map[instance] = memo = Memoized(self.method.__get__(instance, owner), context=self.context)
        return memo


class Reactive[K, V](Subscribable, MutableMapping[K, V]):
    UNSET: V = object()  # type: ignore

    def __hash__(self):
        """
        Returns the hash value of the object based on its unique identifier.
        """
        return id(self)

    def _null(self):
        """
        Creates a new Signal initialized with the unset sentinel value.

        Returns:
            A Signal object with its value set to UNSET and configured for equality checking and context.
        """
        return Signal(self.UNSET, self._check_equality, context=self.context)

    def __init__(self, initial: Mapping[K, V] | None = None, check_equality=True, *, context: Context | None = None):
        """
        Initializes a reactive mapping, optionally with initial key-value pairs.

        Args:
                initial: Optional mapping to pre-populate the reactive dictionary.
                check_equality: If True, value updates will only notify subscribers when the value changes.
                context: Optional reactive context for signal computations.
        """
        super().__init__(context=context)
        self._signals = defaultdict[K, Signal[V]](self._null) if initial is None else defaultdict(self._null, {k: Signal(v, check_equality, context=context) for k, v in initial.items()})
        self._check_equality = check_equality

    def __getitem__(self, key: K):
        """
        Retrieves the value associated with the given key.

        Raises:
            KeyError: If the key is not set in the reactive mapping.
        """
        value = self._signals[key].get()
        if value is self.UNSET:
            raise KeyError(key)
        return value

    def __setitem__(self, key: K, value: V):
        """
        Sets the value for a given key in the reactive mapping.

        If the key was previously unset, notifies subscribers of the change.
        """
        with Batch(force_flush=False, context=self.context):
            old_value = self._signals[key].get(track=False)
            self._signals[key].set(value)
            if old_value is self.UNSET:
                self.notify()

    def __delitem__(self, key: K):
        """
        Removes a key and its value from the reactive mapping.

        Raises:
            KeyError: If the key is not set in the mapping.
        """
        state = self._signals[key]
        if state.get(track=False) is self.UNSET:
            raise KeyError(key)
        with Batch(force_flush=False, context=self.context):
            state.set(self.UNSET)
            self.notify()

    def __iter__(self):
        """
        Returns an iterator over keys in the reactive mapping that have assigned values.

        Only keys whose values are set (not equal to the UNSET sentinel) are included.
        """
        self.track()
        unset = self.UNSET
        return (key for key, signal in self._signals.items() if signal.get(track=False) is not unset)

    def __len__(self):
        """
        Returns the number of keys in the reactive mapping that have set values.

        Tracks dependencies for reactive updates.
        """
        self.track()
        unset = self.UNSET
        return sum(signal.get(track=False) is not unset for signal in self._signals.values())

    def __repr__(self):
        """
        Returns a string representation of the reactive mapping, including only keys with set values.
        """
        self.track()
        unset = self.UNSET
        return repr({k: value for k, v in self._signals.items() if (value := v.get()) is not unset})

    def items(self):
        """
        Returns a view of key-value pairs for all set entries in the reactive mapping.

        Only keys with values that are currently set (not unset) are included in the returned items view.
        """
        self.track()
        unset = self.UNSET
        return ({k: v for k, signal in self._signals.items() if (v := signal.get()) is not unset}).items()


class DerivedProperty[T, I]:
    def __init__(self, method: Callable[[I], T], *, context: Context | None = None):
        """
        Initializes the descriptor for a derived reactive property.

        Args:
            method: The instance method used to compute the derived value.
            context: Optional context for managing reactive computations.
        """
        super().__init__()
        self.method = method
        self.map = WeakKeyDictionary[I, Derived[T]]()
        self.context = context

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self:
        """
        Returns the descriptor itself when accessed on the class rather than an instance.
        """

    @overload
    def __get__(self, instance: I, owner: type[I]) -> T:
        """
        Returns the memoized value for the given instance, computing and caching it if necessary.

        If accessed on the class, returns the descriptor itself.
        """

    def __get__(self, instance: I | None, owner):
        """
        Returns the derived value for the given instance, creating and caching a Derived computation if necessary.

        If accessed on the class, returns the descriptor itself.
        """
        if instance is None:
            return self
        if func := self.map.get(instance):
            return func()
        self.map[instance] = func = Derived(self.method.__get__(instance, owner), context=self.context)
        return func()


class DerivedMethod[T, I]:
    def __init__(self, method: Callable[[I], T], check_equality=True, *, context: Context | None = None):
        """
        Initializes the DerivedMethod descriptor with the provided method and configuration.

        Args:
            method: The instance method to be wrapped as a derived computation.
            check_equality: Whether to perform equality checks when updating the derived value.
            context: Optional context to use for the derived computation.
        """
        super().__init__()
        self.method = method
        self.check_equality = check_equality
        self.map = WeakKeyDictionary[I, Derived[T]]()
        self.context = context

    @overload
    def __get__(self, instance: None, owner: type[I]) -> Self:
        """
        Returns the descriptor itself when accessed on the class rather than an instance.
        """

    @overload
    def __get__(self, instance: I, owner: type[I]) -> Derived[T]:
        """
        Returns the derived computation for the given instance, creating it if necessary.

        If accessed on the class, returns the descriptor itself.
        """

    def __get__(self, instance: I | None, owner):
        """
        Returns the derived computation for the given instance, creating and caching it if necessary.

        If accessed on the class, returns the descriptor itself. Otherwise, retrieves or creates a `Derived` object wrapping the bound method for the instance, with optional equality checking and context.
        """
        if instance is None:
            return self
        if func := self.map.get(instance):
            return func

        self.map[instance] = func = Derived(self.method.__get__(instance, owner), self.check_equality, context=self.context)
        return func
