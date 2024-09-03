import builtins
from functools import cache, wraps
from inspect import Signature, getsource
from os import getenv

import micropip
from js import window

from .package import get_package_name
from .toast import loading


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

        with loading(f"pip install {' '.join(r)}"):
            return await install(*args, **kwargs)

    micropip.install = install_with_toast


@cache
def patch_linecache():
    import linecache

    source = getsource(linecache).replace(" or (filename.startswith('<') and filename.endswith('>'))", "", 1)
    exec(source, linecache.__dict__)


@cache
def patch_console():
    from pyodide.console import Console, PyodideConsole

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
    def input(prompt=""):
        return window.prompt(str(prompt)) or ""

    builtins.input = input


@cache
def patch_exit():
    window.close.__signature__ = Signature()  # type: ignore
    builtins.exit = builtins.quit = window.close


patch_install()
patch_linecache()
patch_console()
patch_input()
patch_exit()
