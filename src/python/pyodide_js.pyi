from pyodide.ffi import JsProxy

class _Lockfile:
    packages: JsProxy

lockfile: _Lockfile
loadedPackages: JsProxy  # noqa: N816

async def loadPackagesFromImports(source: str): ...  # noqa: N802
