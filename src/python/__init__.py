from asyncio import ensure_future

from __main__ import *

from .app.utils.patches import patch_console, patch_input, patch_install


def register_to_globals(value, name=""):
    import __main__

    __main__.__dict__[name or value.__name__] = value


async def asynchronous_bootstrap():
    from micropip import install

    await install(["promplate==0.3.4.8", "promplate-pyodide==0.0.3.3"])

    from promplate_pyodide import patch_all

    await patch_all()  # type: ignore

    from .app.explain import explain

    register_to_globals(explain)


def main():
    from .app import console

    register_to_globals(console, "consoleModule")

    patch_install()
    patch_input()
    patch_console()

    return ensure_future(asynchronous_bootstrap())
