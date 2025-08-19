from collections import defaultdict
from collections.abc import Mapping, MutableMapping

from .context import Context, default_context
from .primitives import Signal, Subscribable, _equal


class ReactiveMappingProxy[K, V](MutableMapping[K, V]):
    def _signal(self, value=False):
        return Signal(value, context=self.context)  # 0 for unset

    def __init__(self, initial: MutableMapping[K, V], check_equality=True, *, context: Context | None = None):
        self.context = context or default_context
        self._check_equality = check_equality
        self._data = initial
        self._keys = defaultdict(self._signal, {k: self._signal(True) for k in initial})
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
        return sum(i._value for i in self._keys.values())  # noqa: SLF001

    def __repr__(self):
        return repr({**self})


class ReactiveMapping[K, V](ReactiveMappingProxy[K, V]):
    def __init__(self, initial: Mapping[K, V] | None = None, check_equality=True, *, context: Context | None = None):
        super().__init__({**initial} if initial is not None else {}, check_equality, context=context)
