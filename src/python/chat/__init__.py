async def asynchronous_bootstrap():
    from micropip import install

    await install(["promplate==0.3.4.8", "promplate-pyodide==0.0.3.3"])

    from promplate_pyodide import patch_all

    await patch_all()
