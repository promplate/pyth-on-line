from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

from pyodide.ffi import JsArray, to_js

if TYPE_CHECKING:
    from .item import Item

type Callback = Callable[[JsArray[Item]]]


class WriteStream:
    def __init__(self, type, items: list[Item], sync: Callable[[]]):
        self.name = f"<std{type}>"

        self._type: Literal["out", "err"] = type
        self._items = items
        self._sync = sync

    def write(self, text: str):
        if not self._items or self._items[-1]["type"] != self._type:
            self._items.append({"type": self._type, "text": text})
        else:
            self._items[-1]["text"] += text

        self._sync()

    def flush(self): ...

    def isatty(self):
        return True


class StreamManager:
    def __init__(self, callback: Callback):
        items: list[Item] = []
        self.stdout = WriteStream("out", items, self.sync)
        self.stderr = WriteStream("err", items, self.sync)
        self.items = items

        self.callback = callback

    def sync(self):
        self.callback(to_js(self.items))
