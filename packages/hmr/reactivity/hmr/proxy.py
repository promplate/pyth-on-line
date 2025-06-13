from collections.abc import MutableMapping
from typing import Any

from ..context import Context
from ..helpers import Reactive


class Proxy[T: MutableMapping](Reactive[str, Any]):
    def __init__(self, initial: T, check_equality=True, *, context: Context | None = None):
        super().__init__(initial, check_equality, context=context)
        self.raw: T = initial

    def __setitem__(self, key, value):
        self.raw[key] = value
        super().__setitem__(key, value)

    def __delitem__(self, key):
        del self.raw[key]
        super().__delitem__(key)
