from collections.abc import Callable

from reactivity.context import Context

from ..primitives import BaseDerived, _equal


class Dirty[T](BaseDerived[T]):
    UNSET = object()

    def __init__(self, fn: Callable[[], T], *, context: Context | None = None):
        super().__init__(context=context)
        self.fn = fn
        self.value = __class__.UNSET

    def trigger(self):
        self.track()
        with self._enter():
            value = self.fn()
            if not _equal(value, self.value):
                self.value = value
                self.notify()  # BUG: b -> a <- (b, c) will cause Dirty a to re-evaluate by c
            return value
