import builtins
from functools import cached_property
from pprint import pformat
from typing import TYPE_CHECKING

from pyodide.console import ConsoleFuture, PyodideConsole

from .bridge import js_api
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
    @cached_property
    def builtins(self):
        return builtins.__dict__.copy()

    @cached_property
    def context(self):
        return ConsoleContext({"__builtins__": self.builtins, "__name__": "__main__", "__doc__": None, "__package__": None, "__loader__": None, "__spec__": None})

    @cached_property
    def console(self):
        return EnhancedConsole(self.context)

    @js_api
    def complete(self, source: str):
        return self.console.complete(source)

    def push(self, line: str):
        res = Result(future := self.console.push(line))

        @future.add_done_callback
        def _(_):
            if future.syntax_check == "complete" and future.exception() is None:
                self.builtins["_"] = future.result()

        return res

    def pop(self):
        assert self.console.buffer
        self.console.buffer.pop()
