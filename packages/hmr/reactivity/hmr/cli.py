import sys
from pathlib import Path

from .core import SyncReloader


def cli(args: list[str] | None = None):
    if args is None:
        args = sys.argv[1:]

    if len(args) < 1:
        print("\n Usage: hmr <entry file>, just like python <entry file>")
        print(" Usage: hmr -m <module>, just like python -m <module>\n")
        exit(1)

    # Handle -m flag for module execution
    if args[0] == "-m":
        if len(args) < 2:
            print("\n Usage: hmr -m <module>, just like python -m <module>\n")
            exit(1)

        module_name = args[1]
        args.pop(0)  # remove -m flag

        if (cwd := str(Path.cwd())) not in sys.path:
            sys.path.insert(0, cwd)

        # Find the module using importlib
        import importlib.util

        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                print(f"Error: No module named '{module_name}'")
                exit(1)

            # Check if it's a package (has submodule_search_locations)
            if spec.submodule_search_locations:
                # It's a package, look for __main__.py
                main_spec = importlib.util.find_spec(f"{module_name}.__main__")
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
            print(f"Error: {e}")
            exit(1)
        args[0] = entry
    else:
        # Original file-based behavior
        entry = args[0]
        if not (path := Path(entry)).is_file():
            raise FileNotFoundError(path.resolve())
        path = Path(entry)
        sys.path.insert(0, str(path.parent.resolve()))

    _argv = sys.argv[:]
    sys.argv[:] = args
    try:
        reloader = SyncReloader(entry)
        sys.modules["__main__"] = reloader.entry_module
        reloader.keep_watching_until_interrupt()
    finally:
        sys.argv[:] = _argv
