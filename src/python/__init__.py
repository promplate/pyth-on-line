from asyncio import get_running_loop
from functools import wraps
from os import getenv
from pathlib import Path
from re import compile
from typing import TYPE_CHECKING

import micropip
from micropip import install
from micropip.package_index import INDEX_URLS
from pyodide.ffi import create_once_callable

from __main__ import *

if TYPE_CHECKING:
    from stub import with_toast


if index_url := getenv("PYPI_INDEX_URL"):
    INDEX_URLS.insert(0, index_url)

pattern = compile(r"[\w-]+")


def get_package_name(package: str):
    if package.endswith(".whl"):
        return Path(package).stem

    if match := pattern.search(package):
        return match.group()
    else:
        return package


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


def register_to_globals(value, name=""):
    import __main__

    __main__.__dict__[name or value.__name__] = value


async def asynchronous_bootstrap():
    await install_with_toast(["promplate==0.3.4.8", "promplate-pyodide==0.0.3.3"])

    from promplate_pyodide import patch_all

    await patch_all()  # type: ignore

    from .app.explain import explain

    register_to_globals(explain)


def main():
    from .app import console

    register_to_globals(console, "consoleModule")

    return get_running_loop().create_task(asynchronous_bootstrap())
