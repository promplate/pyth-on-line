import builtins
from collections import ChainMap
from functools import cached_property

from pyodide.console import ConsoleFuture, PyodideConsole

from .utils.bridge import js_api


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


class Console:
    @cached_property
    def builtins_layer(self):
        return {"__name__": "__main__", "__builtins__": builtins}

    @cached_property
    def console(self):
        context = ConsoleGlobals({}, self.builtins_layer)

        if __debug__:
            import __main__

            context.maps.append(__main__.__dict__)

        return PyodideConsole(context)

    @js_api
    def complete(self, source: str):
        return self.console.complete(source)

    @js_api
    def push(self, line: str):
        res = Result(future := self.console.push(line))

        @future.add_done_callback
        def _(_):
            if future.syntax_check == "complete" and future.exception() is None:
                self.builtins_layer["_"] = future.result()

        return res
