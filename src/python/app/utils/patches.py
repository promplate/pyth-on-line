from functools import cache

from .lock import with_lock


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
