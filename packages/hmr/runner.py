import asyncio


from reactivity.hmr.run import cli, main, run_module_async, run_path_async, run_module

if __name__ == "__main__":
    # import sys
    # asyncio.run(run_module_async("pytest", ["test_my.py::test_my"]))
    #
    cli()  # test_my.py::test_my --no-header --no-summary -q
    # run_module("pytest", ["test_my.py::test_my"])

