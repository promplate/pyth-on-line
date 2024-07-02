import builtins
from collections import ChainMap
from functools import cached_property
from typing import TYPE_CHECKING

from pyodide.console import ConsoleFuture, PyodideConsole

from .bridge import js_api
from .source import FakeFile


class ConsoleGlobals(ChainMap, dict):  # type: ignore
    def __repr__(self):
        return repr(self.maps[0])


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

        self.fake_file = FakeFile(self.filename)

    def runsource(self, source: str, filename="<console>"):
        fake_source = "\n" * (len(self.fake_file.lines) - len(self.buffer) + 1) + source
        self.fake_file.push(self.buffer[-1])

        future = super().runsource(fake_source, filename)

        return future

    def pop(self):
        assert self.buffer
        self.buffer.pop()
        self.fake_file.pop()


class ConsoleAPI:
    @cached_property
    def builtins_layer(self):
        return {"__name__": "__main__", "__builtins__": builtins, "__doc__": None}

    @cached_property
    def console(self):
        context = ConsoleGlobals({}, self.builtins_layer)

        if __debug__:
            import __main__

            if TYPE_CHECKING:
                from ..stub import toast
            else:
                toast = __main__.toast

            class Proxy(dict):
                def __getitem__(self, key: str):
                    res = __main__.__dict__[key]  # raise KeyError if not found
                    toast.warning(f"used {key} from __main__")
                    return res

            context.maps.append(Proxy())

        return EnhancedConsole(context)

    @js_api
    def complete(self, source: str):
        return self.console.complete(source)

    def push(self, line: str):
        res = Result(future := self.console.push(line))

        @future.add_done_callback
        def _(_):
            if future.syntax_check == "complete" and future.exception() is None:
                self.builtins_layer["_"] = future.result()

        return res
