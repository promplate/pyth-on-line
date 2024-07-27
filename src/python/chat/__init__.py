from asyncio import ensure_future
from operator import call


@ensure_future
@call
async def install_requirements():
    from micropip import install

    await install(["promplate==0.3.4.8", "promplate-pyodide==0.0.3.4"])

    from promplate_pyodide import patch_all

    await patch_all()
