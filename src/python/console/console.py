from __future__ import annotations

import builtins
from ast import literal_eval, parse
from asyncio import ensure_future
from collections.abc import Callable
from contextlib import suppress
from functools import cached_property
from operator import call
from pprint import pformat
from typing import TYPE_CHECKING

from js import window
from pyodide.console import ConsoleFuture, PyodideConsole

from .bridge import js_api
from .eval import install_pure_eval
from .source import SourceFile


class ConsoleContext(dict):
    def __repr__(self):
        return pformat({k: v for k, v in self.items() if k != "__builtins__"})

    if __debug__:

        def __missing__(self, key: str):
            import __main__

            if TYPE_CHECKING:
                from ..stub import toast
            else:
                toast = __main__.toast

            res = __main__.__dict__[key]  # raise KeyError if not found
            toast.warning(f"used {key} from __main__")
            return res


class Result:
    def __init__(self, future: ConsoleFuture):
        self.future = future
        self.status = future.syntax_check

        future.add_done_callback(lambda fut: fut.exception())  # to prevent an annoying warning

    @property
    def formatted_error(self):
        if self.status == "syntax-error":
            return f"Traceback (most recent call last):\n{self.future.formatted_error}"
        return self.future.formatted_error

    async def get_repr(self):
        res = await self.future
        if res is not None:
            return repr(res)


class EnhancedConsole(PyodideConsole):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.file = SourceFile(self.filename)

    def runsource(self, source: str, filename="<console>"):
        fake_source = self.file.shift_source(source)

        future = super().runsource(fake_source, filename)

        if future.syntax_check != "incomplete":
            self.file.push(source)

        return future


class ConsoleAPI:
    def __init__(self, sync: Callable[[]]):
        self.sync = sync
        self.console.stdin_callback = window.prompt  # type: ignore
        self.console.stdout_callback = lambda output: self.push_item({"type": "out", "text": output})  # type: ignore
        self.console.stderr_callback = lambda output: self.push_item({"type": "err", "text": output, "is_traceback": False})  # type: ignore
        self.incomplete = False

    @cached_property
    def builtins(self):
        return builtins.__dict__.copy()

    @cached_property
    def context(self):
        return ConsoleContext({"__builtins__": self.builtins, "__name__": "__main__", "__doc__": None, "__package__": None, "__loader__": None, "__spec__": None})

    @cached_property
    def console(self):
        return EnhancedConsole(self.context)

    if TYPE_CHECKING:
        from .item import Item

    @cached_property
    def items(self) -> list[Item]:
        return []

    @js_api
    def complete(self, source: str):
        return self.console.complete(source)

    @js_api
    def get_items(self) -> list[Item]:
        if self.incomplete:
            assert self.console.buffer
            return [*self.items, {"type": "in", "text": "\n".join(self.console.buffer), "incomplete": True}]
        return self.items

    @staticmethod
    def can_merge(last: Item, this: Item):
        if last["type"] != this["type"]:
            return False
        if last["type"] == "out":  # both stdout
            return True
        if last["type"] == "err" and not last.get("is_traceback", False) and not this.get("is_traceback", False):  # both stderr
            return True

    def push_item(self, item: Item, behind: Item | None = None):
        assert item["type"] != "in"  # input should be pushed by push method

        if not self.items:
            assert behind is None
            self.items.append(item)
            self.sync()
            return

        last = self.items[-1]

        if self.can_merge(last, item):
            last["text"] += f"\n{item["text"]}" if item["type"] == "in" else item["text"]
            self.sync()
            return last

        elif behind is not None:
            # not stdout/stderr
            index = -1
            for index, i in enumerate(self.items):
                if i is behind:
                    break
            assert index != -1, "not found"

            if index != len(self.items) - 1 and self.items[index + 1]["type"] in ("out", "err"):
                assert self.items[index + 1].get("is_traceback", False) is False, "traceback should only be one"
                index += 1  # repr follows stdout
            self.items.insert(index + 1, item)

        else:
            self.items.append(item)

        self.sync()

    def push(self, line: str):
        source = "\n".join((*self.console.buffer, line)) if self.incomplete else line  # must run before pushing because after that buffer will be empty
        res = Result(future := self.console.push(line))
        self.incomplete = future.syntax_check == "incomplete"
        self.sync()

        if res.status != "incomplete":
            self.items.append(input_item := {"type": "in", "text": source})

            if res.status == "syntax-error":
                assert res.formatted_error
                self.push_item({"type": "err", "text": res.formatted_error, "is_traceback": True}, behind=input_item)
            elif res.status == "complete":
                self.sync()

                @ensure_future
                @call
                async def _():
                    try:
                        if text := await res.get_repr():
                            self.push_item({"type": "repr", "text": text}, behind=input_item)
                            self.builtins["_"] = res.future.result()
                    except Exception as e:
                        stderr = res.formatted_error or self.console.formattraceback(e)
                        self.push_item({"type": "err", "text": stderr, "is_traceback": True}, behind=input_item)

        return res

    def pop(self):
        assert self.console.buffer
        line = self.console.buffer.pop()

        if not self.console.buffer:
            self.incomplete = False

        self.sync()

        return line

    @staticmethod
    def _inspect(value):
        res = {"class": type(value).__qualname__}

        match value:
            case type():
                res |= {
                    "value": f"{value.__qualname__}({', '.join(cls.__qualname__ for cls in value.__bases__)})",
                    "type": "exception" if issubclass(value, BaseException) else "class",
                }
            case _:
                res |= {"value": repr(value)}

        return res

    @js_api
    def inspect(self, name: str):
        if name.isidentifier():
            if name in self.context or name in self.builtins:
                return self._inspect(self.context.get(name) or self.builtins[name])
            return

        with suppress(ValueError, SyntaxError):
            return self._inspect(literal_eval(name))

        if install_pure_eval().done():
            with suppress(ValueError):
                return self._inspect(self.literal_eval(name))

    def literal_eval(self, source: str):
        from pure_eval.core import Evaluator
        from pure_eval.utils import CannotEval

        with suppress(CannotEval, SyntaxError):
            if value := getattr(parse(source).body[0], "value", None):
                return Evaluator(self.context)[value]

        raise ValueError
