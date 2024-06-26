from functools import cache, wraps
from inspect import getsource
from os import getenv
from typing import TYPE_CHECKING

import micropip
from pyodide.ffi import create_once_callable

from .lock import with_lock
from .package import get_package_name

if TYPE_CHECKING:
    from stub import with_toast
else:
    from __main__ import with_toast


@cache
def patch_install():
    from micropip import install
    from micropip.package_index import INDEX_URLS

    if index_url := getenv("PYPI_INDEX_URL"):
        INDEX_URLS.insert(0, index_url)

    @wraps(install)
    async def install_with_toast(*args, **kwargs):
        r = kwargs.get("requirements") or args[0]
        r = [r] if isinstance(r, str) else r
        r = list(map(get_package_name, r))

        @with_toast(loading=f"pip install {' '.join(r)}")
        @create_once_callable
        async def _():
            return install(*args, **kwargs)

        return await _()  # type: ignore

    micropip.install = install_with_toast


@cache
def patch_linecache():
    import linecache

    source = getsource(linecache).replace(" or (filename.startswith('<') and filename.endswith('>'))", "", 1)
    exec(source, linecache.__dict__)


@cache
def patch_console():
    from pyodide.console import Console, PyodideConsole

    @with_lock
    @wraps(PyodideConsole.runcode)
    async def runcode(self: PyodideConsole, source: str, code):
        from .imports import find_packages_to_install

        packages = find_packages_to_install(source)
        if packages:
            await micropip.install(packages)

        return await Console.runcode(self, source, code)

    PyodideConsole.runcode = runcode


@cache
def patch_input():
    import builtins

    def input(prompt=""):
        from js import window

        return window.prompt(prompt) or ""

    builtins.input = input


patch_install()
patch_linecache()
patch_console()
patch_input()
