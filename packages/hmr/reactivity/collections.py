from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, MutableMapping, MutableSequence, MutableSet, Sequence, Set
from functools import update_wrapper
from inspect import isclass, ismethod
from typing import Any, overload

from .context import Context, default_context
from .primitives import Derived, Effect, Signal, Subscribable, _equal


class ReactiveMappingProxy[K, V](MutableMapping[K, V]):
    def _signal(self, value=False):
        return Signal(value, context=self.context)  # False for unset

    def __init__(self, initial: MutableMapping[K, V], check_equality=True, *, context: Context | None = None):
        self.context = context or default_context
        self._check_equality = check_equality
        self._data = initial
        self._keys = defaultdict(self._signal, {k: self._signal(True) for k in tuple(initial)})  # in subclasses, self._signal() may mutate `initial`
        self._iter = Subscribable()

    def __getitem__(self, key: K):
        if self._keys[key].get():
            return self._data[key]
        raise KeyError(key)

    def __setitem__(self, key: K, value: V):
        if self._keys[key]._value:  # noqa: SLF001
            should_notify = not self._check_equality or not _equal(self._data[key], value)
            self._data[key] = value
            if should_notify:
                self._keys[key].notify()
        else:
            self._data[key] = value
            with self.context.batch(force_flush=False):
                self._keys[key].set(True)
                self._iter.notify()

    def __delitem__(self, key: K):
        if not self._keys[key]._value:  # noqa: SLF001
            raise KeyError(key)
        del self._data[key]
        with self.context.batch(force_flush=False):
            self._keys[key].set(False)
            self._iter.notify()

    def __iter__(self):
        self._iter.track()
        for key in self._keys:
            if self._keys[key]._value:  # noqa: SLF001
                yield key

    def __len__(self):
        self._iter.track()
        return len(self._data)

    def __repr__(self):
        return repr({**self})


class ReactiveMapping[K, V](ReactiveMappingProxy[K, V]):
    def __init__(self, initial: Mapping[K, V] | None = None, check_equality=True, *, context: Context | None = None):
        super().__init__({**initial} if initial is not None else {}, check_equality, context=context)


class ReactiveSetProxy[T](MutableSet[T]):
    def _signal(self, value=False):
        return Signal(value, self._check_equality, context=self.context)  # False for unset

    def __init__(self, initial: MutableSet[T], check_equality=True, *, context: Context | None = None):
        self.context = context or default_context
        self._check_equality = check_equality
        self._data = initial
        self._items = defaultdict(self._signal, {k: self._signal(True) for k in tuple(initial)})
        self._iter = Subscribable()

    def __contains__(self, value):
        return self._items[value].get()

    def add(self, value):
        with self.context.batch(force_flush=False):
            if self._items[value].set(True):
                self._data.add(value)
                self._iter.notify()

    def discard(self, value):
        if value in self._items and (signal := self._items[value]) and signal._value:  # noqa: SLF001
            self._data.remove(value)
            with self.context.batch(force_flush=False):
                signal.set(False)
                self._iter.notify()

    def remove(self, value):
        if value in self._items and (signal := self._items[value]) and signal._value:  # noqa: SLF001
            self._data.remove(value)
            with self.context.batch(force_flush=False):
                signal.set(False)
                self._iter.notify()
        else:
            raise KeyError(value)

    def __iter__(self):
        self._iter.track()
        for item in self._items:
            if self._items[item]._value:  # noqa: SLF001
                yield item

    def __len__(self):
        self._iter.track()
        return len(self._data)

    def __repr__(self):
        return repr({*self})


class ReactiveSet[T](ReactiveSetProxy[T]):
    def __init__(self, initial: Set[T] | None = None, check_equality=True, *, context: Context | None = None):
        super().__init__({*initial} if initial is not None else set(), check_equality, context=context)


def _weak_derived[T](fn: Callable[[], T], check_equality=True, *, context: Context | None = None):
    d = Derived(fn, check_equality, context=context)
    s = d.subscribers = ReactiveSetProxy(d.subscribers)  # type: ignore
    e = Effect(lambda: not s and d.dispose(), False)  # when `subscribers` is empty, gc it
    s._iter.subscribers.add(e)  # noqa: SLF001
    e.dependencies.add(s._iter)  # noqa: SLF001
    return d


class ReactiveSequenceProxy[T](MutableSequence[T]):
    def _signal(self):
        return Subscribable(context=self.context)

    def __init__(self, initial: MutableSequence[T], check_equality=True, *, context: Context | None = None):
        self.context = context or default_context
        self._check_equality = check_equality
        self._data = initial
        self._keys = keys = defaultdict(self._signal)  # positive and negative index signals
        self._iter = Subscribable()
        self._length = len(initial)

        for index in range(-len(initial), len(initial)):
            keys[index] = self._signal()

    @overload
    def __getitem__(self, key: int) -> T: ...
    @overload
    def __getitem__(self, key: slice) -> list[T]: ...

    def __getitem__(self, key: int | slice):
        if isinstance(key, slice):
            start, stop, step = key.indices(self._length)
            if step != 1:
                raise NotImplementedError  # TODO
            for i in range(start, stop):
                self._keys[i].track()
            if not self._check_equality:
                self._iter.track()
                return self._data[start:stop]
            # The following implementation is inefficient but works. TODO: refactor this
            return _weak_derived(lambda: (self._iter.track(), self._data[slice(*key.indices(self._length))])[1])()

        else:
            # Handle integer indices
            self._keys[key].track()
            if -self._length <= key < self._length:
                return self._data[key]
            raise IndexError(key)

    def _replace(self, range_slice: slice, target: Iterable[T]):
        start, stop, step = range_slice.indices(self._length)
        if step != 1:
            raise NotImplementedError  # TODO

        target = [*target]
        assert start <= stop
        delta = len(target) - (stop - start)

        with self.context.batch(force_flush=False):
            if delta > 0:
                if not self._check_equality:
                    for i in range(start, self._length + delta):
                        self._keys[i].notify()
                    for i in range(stop + delta):
                        self._keys[i - self._length - delta].notify()
                else:
                    for i in range(start, self._length + delta):
                        if i < self._length:
                            if i - start < len(target):
                                if _equal(self._data[i], target[i - start]):
                                    continue
                            else:
                                if _equal(self._data[i], self._data[i - delta]):
                                    continue
                        self._keys[i].notify()
                    for i in range(stop + delta):
                        if i >= delta:
                            if i >= start:
                                if _equal(self._data[i - self._length - delta], target[i - start]):
                                    continue
                            else:
                                if _equal(self._data[i - self._length - delta], self._data[i - self._length]):
                                    continue
                        self._keys[i - self._length - delta].notify()

            elif delta < 0:
                if not self._check_equality:
                    for i in range(start, self._length):
                        self._keys[i].notify()
                    for i in range(stop):
                        self._keys[i - self._length].notify()
                else:
                    for i in range(start, self._length):
                        if i < self._length + delta:
                            if i - start < len(target):
                                if _equal(self._data[i], target[i - start]):
                                    continue
                            else:
                                if _equal(self._data[i], self._data[i - delta]):
                                    continue
                        self._keys[i].notify()
                    for i in range(stop):
                        if i >= -delta:
                            if 0 <= i - start < len(target):
                                if _equal(self._data[i - self._length], target[i - start]):
                                    continue
                            else:
                                if _equal(self._data[i - self._length], self._data[i - self._length + delta]):
                                    continue
                        self._keys[i - self._length].notify()

            else:
                if not self._check_equality:
                    for i in range(start, stop):
                        self._data[i] = target[i - start]
                        self._keys[i].notify()
                        self._keys[i - self._length].notify()
                else:
                    for i in range(start, stop):
                        original = self._data[i]
                        if not _equal(original, target[i - start]):
                            self._data[i] = target[i - start]
                            self._keys[i].notify()
                            self._keys[i - self._length].notify()

            if delta:
                self._length += delta
                self._iter.notify()
            self._data[start:stop] = target

    def __len__(self):
        self._iter.track()
        return self._length

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            self._replace(key, value)
        else:
            if key < 0:
                key += self._length
            if not 0 <= key < self._length:
                raise IndexError(key)
            self._replace(slice(key, key + 1), [value])

    def __delitem__(self, key):
        if isinstance(key, slice):
            self._replace(key, [])
        else:
            if key < 0:
                key += self._length
            if not 0 <= key < self._length:
                raise IndexError(key)
            self._replace(slice(key, key + 1), [])

    def insert(self, index, value):
        if index < 0:
            index += self._length
        if index < 0:
            index = 0
        if index > self._length:
            index = self._length
        self._replace(slice(index, index), [value])

    def append(self, value):
        self._replace(slice(self._length, self._length), [value])

    def extend(self, values):
        self._replace(slice(self._length, self._length), values)

    def pop(self, index=-1):
        if index < 0:
            index += self._length
        if not 0 <= index < self._length:
            raise IndexError(index)
        value = self._data[index]
        self._replace(slice(index, index + 1), [])
        return value

    def remove(self, value):
        for i in range(self._length):
            if self._data[i] == value:
                self._replace(slice(i, i + 1), [])
                return
        raise ValueError(value)

    def clear(self):
        self._replace(slice(0, self._length), [])

    def reverse(self):
        self._replace(slice(0, self._length), reversed(self._data))

    def sort(self, *, key=None, reverse=False):
        self._replace(slice(0, self._length), sorted(self._data, key=key, reverse=reverse))  # type: ignore

    def __repr__(self):
        return repr([*self])

    def __eq__(self, value):
        return [*self] == value


class ReactiveSequence[T](ReactiveSequenceProxy[T]):
    def __init__(self, initial: Sequence[T] | None = None, check_equality=True, *, context: Context | None = None):
        super().__init__([*initial] if initial is not None else [], check_equality, context=context)


# TODO: use WeakKeyDictionary to avoid memory leaks


def reactive_object_proxy[T](initial: T, check_equality=True, *, context: Context | None = None) -> T:
    context = context or default_context

    names = ReactiveMappingProxy(initial.__dict__, check_equality, context=context)  # TODO: support classes with `__slots__`
    _iter = names._iter  # noqa: SLF001
    _keys: defaultdict[str, Signal[bool | None]] = names._keys  # noqa: SLF001  # type: ignore
    # true for instance attributes, false for non-existent attributes, None for class attributes
    # only instance attributes are visible in `__dict__`
    # TODO: accessing non-data descriptors should be treated as getting `Derived` instead of `Signal`
    CLASS_ATTR = None  # sentinel for class attributes  # noqa: N806

    cls = initial.__class__
    meta: type[type[T]] = type(cls)

    class Proxy(cls, metaclass=meta):
        def __getattribute__(self, key):
            if key == "__dict__":
                return names
            if _keys[key].get():
                res = getattr(initial, key)
                if ismethod(res):
                    return res.__func__.__get__(self)
                return res
            return super().__getattribute__(key)

        def __setattr__(self, key: str, value):
            if _keys[key]._value is not False:  # noqa: SLF001
                should_notify = not check_equality or not _equal(getattr(initial, key), value)
                setattr(initial, key, value)
                if should_notify:
                    _keys[key].notify()
            else:
                setattr(initial, key, value)
                with context.batch(force_flush=False):
                    _keys[key].set(True if key in initial.__dict__ else CLASS_ATTR)  # non-instance attributes are tracked but not visible in `__dict__`
                    _iter.notify()

        def __delattr__(self, key):
            if not _keys[key]._value:  # noqa: SLF001
                raise AttributeError(key)
            delattr(initial, key)
            with context.batch(force_flush=False):
                _keys[key].set(False)
                _iter.notify()

        def __dir__(self):
            _iter.track()
            return dir(initial)

        if isclass(initial):
            __new__ = meta.__new__

            def __call__(self, *args, **kwargs):
                # TODO: refactor this because making a new class whenever constructing a new instance is wasteful
                return reactive(initial(*args, **kwargs), check_equality, context=context)  # type: ignore

            # it seems that __str__ and __repr__ are not looked up on the class, so we have to define them here
            # note that this do loses reactivity but probably nobody needs reactive stringifying of classes themselves

            def __str__(self):
                return str(initial)

            def __repr__(self):
                return repr(initial)

        else:

            def __init__(self, *args, **kwargs):
                nonlocal bypassed
                if bypassed:
                    bypassed = False
                    return
                super().__init__(*args, **kwargs)

    bypassed = True

    update_wrapper(Proxy, cls, updated=())

    if isclass(initial):
        return Proxy(initial.__name__, (initial,), {**initial.__dict__})  # type: ignore

    return Proxy()  # type: ignore


@overload
def reactive[K, V](value: MutableMapping[K, V], check_equality=True, *, context: Context | None = None) -> ReactiveMappingProxy[K, V]: ...  # type: ignore
@overload
def reactive[K, V](value: Mapping[K, V], check_equality=True, *, context: Context | None = None) -> ReactiveMapping[K, V]: ...
@overload
def reactive[T](value: MutableSet[T], check_equality=True, *, context: Context | None = None) -> ReactiveSetProxy[T]: ...  # type: ignore
@overload
def reactive[T](value: Set[T], check_equality=True, *, context: Context | None = None) -> ReactiveSet[T]: ...
@overload
def reactive[T](value: MutableSequence[T], check_equality=True, *, context: Context | None = None) -> ReactiveSequenceProxy[T]: ...  # type: ignore
@overload
def reactive[T](value: Sequence[T], check_equality=True, *, context: Context | None = None) -> ReactiveSequence[T]: ...
@overload
def reactive[T](value: T, check_equality=True, *, context: Context | None = None) -> T: ...


def reactive(value: Mapping | Set | Sequence | Any, check_equality=True, *, context: Context | None = None):
    match value:
        case MutableMapping():
            return ReactiveMappingProxy(value, check_equality, context=context)
        case Mapping():
            return ReactiveMapping(value, check_equality, context=context)
        case MutableSet():
            return ReactiveSetProxy(value, check_equality, context=context)
        case Set():
            return ReactiveSet(value, check_equality, context=context)
        case MutableSequence():
            return ReactiveSequenceProxy(value, check_equality, context=context)
        case Sequence():
            return ReactiveSequence(value, check_equality, context=context)
        case _:
            return reactive_object_proxy(value, check_equality, context=context)


# TODO: implement deep_reactive, lazy_reactive, etc.
