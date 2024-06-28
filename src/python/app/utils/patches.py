from functools import cache
from inspect import getsource

from .lock import with_lock


@cache
def patch_linecache():
    import linecache

    source = getsource(linecache).replace(" or (filename.startswith('<') and filename.endswith('>'))", "", 1)
    exec(source, linecache.__dict__)


@cache
def patch_console():
    from pyodide.console import PyodideConsole

    PyodideConsole.runcode = with_lock(PyodideConsole.runcode)


@cache
def patch_input():
    import builtins

    def input(prompt=""):
        from js import window

        return window.prompt(prompt) or ""

    builtins.input = input
