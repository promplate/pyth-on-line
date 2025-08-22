import sys
from pathlib import Path


def cli(args: list[str] | None = None):
    if args is None:
        args = sys.argv[1:]

    if len(args) < 1:
        print("\n Usage:")
        print("   hmr <entry file>, just like python <entry file>")
        print("   hmr -m <module>, just like python -m <module>\n")
        exit(1)

    if args[0] == "-m":
        if len(args) < 2:
            print("\n Usage: hmr -m <module>, just like python -m <module>\n")
            exit(1)

        module_name = args[1]
        args.pop(0)  # remove -m flag

        if (cwd := str(Path.cwd())) not in sys.path:
            sys.path.insert(0, cwd)

        from importlib.util import find_spec

        try:
            spec = find_spec(module_name)
            if spec is None:
                print(f"Error: No module named '{module_name}'")
                exit(1)

            if spec.submodule_search_locations:
                # It's a package, look for __main__.py
                main_spec = find_spec(f"{module_name}.__main__")
                if main_spec and main_spec.origin:
                    entry = main_spec.origin
                else:
                    print(f"Error: No module named '{module_name}.__main__'; '{module_name}' is a package and cannot be directly executed")
                    exit(1)
            elif spec.origin is None:
                print(f"Error: Cannot find entry point for module '{module_name}'")
                exit(1)
            else:
                entry = spec.origin
        except ModuleNotFoundError as e:
            print(f"\n {e}\n")
            exit(1)
        args[0] = entry
    else:
        entry = args[0]
        if not (path := Path(entry)).is_file():
            raise FileNotFoundError(path.resolve())
        path = Path(entry)
        sys.path.insert(0, str(path.parent.resolve()))

    from .core import SyncReloader

    _argv = sys.argv[:]
    sys.argv[:] = args
    _main = sys.modules["__main__"]
    try:
        reloader = SyncReloader(entry)
        sys.modules["__main__"] = reloader.entry_module
        reloader.keep_watching_until_interrupt()
    finally:
        sys.argv[:] = _argv
        sys.modules["__main__"] = _main
