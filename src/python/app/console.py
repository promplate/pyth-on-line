import builtins
from collections import ChainMap
from functools import cached_property

from pyodide.console import ConsoleFuture, PyodideConsole
from pyodide.ffi import JsArray, to_js

from .utils.bridge import JsAPI, js_api


async def get_wrapped(future: ConsoleFuture):
    res = await future
    return to_js([res, None if res is None else repr(res)], depth=1)


def input(prompt=""):
    from js import window

    return window.prompt(prompt) or ""


builtins.input = input


class ConsoleGlobals(ChainMap, dict):  # type: ignore
    def __repr__(self):
        return repr(self.maps[0])


class Result(JsAPI):
    def __init__(self, future: ConsoleFuture):
        super().__init__()
        self.future = future
        self.status = future.syntax_check

    @property
    def formatted_error(self):
        return self.future.formatted_error

    @js_api
    async def get_value_and_repl(self):
        return await get_wrapped(self.future)


class Console(JsAPI):
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
    def complete(self, source: str) -> JsArray:
        return to_js(self.console.complete(source), depth=2)

    @js_api
    def push(self, line: str):
        res = Result(future := self.console.push(line))

        @future.add_done_callback
        def _(_):
            if future.syntax_check == "complete" and (res := future.result()) is not None:
                self.builtins_layer["_"] = res

        return res
