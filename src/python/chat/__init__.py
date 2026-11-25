from asyncio import ensure_future
from operator import call


@ensure_future
@call
async def install_requirements():
    from micropip import install
    from pyodide_js import loadedPackages

    requirements = []

    loaded: dict = loadedPackages.to_py()

    if "promplate" not in loaded:
        requirements.append("promplate==0.3.4.9")
    if "promplate-pyodide" not in loaded:
        requirements.append("promplate-pyodide==0.0.4")

    if requirements:
        await install(requirements)

    from promplate_pyodide import patch_all

    await patch_all()
