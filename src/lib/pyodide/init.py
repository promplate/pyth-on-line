# type: ignore

from functools import partial, wraps
from pathlib import Path
from re import compile
from typing import TYPE_CHECKING

import micropip
from micropip import install
from micropip.package_index import INDEX_URLS
from pyodide.ffi import create_once_callable

if TYPE_CHECKING:
    from stub import with_toast

INDEX_URLS.insert(1, "/simple")

pattern = compile(r"[\w-]+")


def get_package_name(package: str):
    if package.endswith(".whl"):
        return Path(package).stem

    return pattern.search(package).group()


@wraps(install)
async def install_with_toast(*args, **kwargs):
    r = kwargs.get("requirements") or args[0]
    r = [r] if isinstance(r, str) else r
    r = list(map(get_package_name, r))

    @with_toast(loading=f"pip install {' '.join(r)}")
    @create_once_callable
    async def _():
        try:
            return await partial(install, index_urls=["/simple", "https://pypi.org/simple"])(*args, **kwargs)
        except ValueError:
            return await install(*args, **kwargs)

    return await _()


micropip.install = install_with_toast

await install_with_toast(["promplate==0.3.4.4", "promplate-pyodide==0.0.3.2"])

from promplate_pyodide import patch_all

await patch_all()

from promplate import *
from promplate.llm.openai import *
