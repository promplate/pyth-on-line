import sys
from pathlib import Path


def run_path(entry: str, args: list[str]):
    path = Path(entry).resolve()
    if path.is_dir():
        if (main := path / "__main__.py").is_file():
            path = main
        else:
            raise FileNotFoundError(f"No __main__.py file in {path}")  # noqa: TRY003
    elif not path.is_file():
        raise FileNotFoundError(f"No such file named {path}")  # noqa: TRY003

    entry = str(path)
    sys.path.insert(0, str(path.parent))

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


def run_module(module_name: str, args: list[str]):
    if (cwd := str(Path.cwd())) not in sys.path:
        sys.path.insert(0, cwd)

    from importlib.util import find_spec

    spec = find_spec(module_name)
    if spec is None:
        raise ModuleNotFoundError(f"No module named '{module_name}'")  # noqa: TRY003

    if spec.submodule_search_locations:
        # It's a package, look for __main__.py
        spec = find_spec(f"{module_name}.__main__")
        if spec and spec.origin:
            entry = spec.origin
        else:
            raise ModuleNotFoundError(f"No module named '{module_name}.__main__'; '{module_name}' is a package and cannot be directly executed")  # noqa: TRY003
    elif spec.origin is None:
        raise ModuleNotFoundError(f"Cannot find entry point for module '{module_name}'")  # noqa: TRY003
    else:
        entry = spec.origin

    # Replace the first argument with the full path
    args[0] = entry

    from importlib import import_module

    from .core import SyncReloader

    class Reloader(SyncReloader):
        entry_module = None  # type: ignore

        def run_entry_file(self):
            import_module(spec.name)

    _argv = sys.argv[:]
    sys.argv[:] = args
    try:
        reloader = Reloader(entry)
        reloader.keep_watching_until_interrupt()
    finally:
        sys.argv[:] = _argv


def cli(args: list[str] | None = None):
    if args is None:
        args = sys.argv[1:]

    try:
        if len(args) < 1 or "--help" in args or "-h" in args:
            print("\n Usage:")
            print("   hmr <entry file>, just like python <entry file>")
            print("   hmr -m <module>, just like python -m <module>\n")
            if len(args) < 1:
                return 1
        elif args[0] == "-m":
            if len(args) < 2:
                print("\n Usage: hmr -m <module>, just like python -m <module>\n")
                return 1
            module_name = args[1]
            args.pop(0)  # remove -m flag
            run_module(module_name, args)
        else:
            run_path(args[0], args)
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"\n Error: {e}\n")
        return 1

    return 0


def main():
    exit(cli(sys.argv[1:]))
