from pyodide.http import pyfetch


async def fetch(url: str):
    res = await pyfetch(f"/proxy?{url=!s}")
    return await res.text()
