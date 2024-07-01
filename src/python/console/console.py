import builtins
import sys
from collections import ChainMap
from contextlib import suppress
from functools import cached_property
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from pyodide.console import ConsoleFuture, PyodideConsole

from .bridge import js_api


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

        for path in sys.path[:]:
            if (file := Path(path) / self.filename).is_file():
                file.unlink()
                sys.path.remove(path)

        with TemporaryDirectory(delete=False) as tempdir:
            sys.path.append(tempdir)
            self.fake_file = Path(tempdir) / self.filename

        self.line_offset = 0

    def __del__(self):
        with suppress(Exception):
            self.fake_file.unlink()
            sys.path.remove(str(self.fake_file.parent))

    def _append_source_file(self, source: str):
        source += "\n"
        self.line_offset += source.count("\n")

        with self.fake_file.open("a+", encoding="utf-8") as file:
            file.write(source)

    def _redo_append(self, source: str):
        content = self.fake_file.read_text()
        source += "\n"
        self.line_offset -= source.count("\n")

        assert content.endswith(source)
        self.fake_file.write_text(content.removesuffix(source))

    def runsource(self, source: str, filename="<console>"):
        fake_source = "\n" * self.line_offset + source
        self._append_source_file(source)

        future = super().runsource(fake_source, filename)

        @future.add_done_callback
        def _(_):
            if future.syntax_check == "incomplete":
                self._redo_append(source)

        return future

    def pop(self):
        assert self.buffer
        self.buffer.pop()
        self.line_offset -= 1

        source = self.fake_file.read_text()
        self.fake_file.write_text(source[: source.rindex("\n", None, -1) + 1])


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
