from functools import cache, wraps
from inspect import getsource
from os import getenv

import micropip
from pyodide.ffi import can_run_sync, run_sync

from .package import get_package_name
from .toast import loading


@cache
def patch_install():
    from micropip import _package_manager_singleton, install
    from micropip.package_index import DEFAULT_INDEX_URLS

    if index_url := getenv("PYPI_INDEX_URL"):
        DEFAULT_INDEX_URLS.insert(0, index_url)
        _package_manager_singleton.index_urls.insert(0, index_url)

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
def patch_sync():
    import asyncio
    import time
    from asyncio import get_running_loop

    @wraps(run := asyncio.run)
    def _(future, **kwargs):
        if can_run_sync():
            return run_sync(future)
        return run(future, **kwargs)

    asyncio.run = _

    @wraps(run_until_complete := get_running_loop().run_until_complete)
    def _(future):
        if can_run_sync():
            return run_sync(future)
        return run_until_complete(future)

    get_running_loop().run_until_complete = _

    @wraps(sleep := time.sleep)
    def _(duration):
        if can_run_sync():
            return run_sync(asyncio.sleep(duration))
        return sleep(duration)

    time.sleep = _


patch_install()
patch_linecache()
patch_console()
patch_sync()
