import builtins
import sys
from pathlib import Path


def run_path(entry: str, args: list[str]):
    path = Path(entry).resolve()
    if path.is_dir():
        if (__main__ := path / "__main__.py").is_file():
            parent = ""
            path = __main__
        else:
            raise FileNotFoundError(f"No __main__.py file in {path}")  # noqa: TRY003
    elif path.is_file():
        parent = None
    else:
        raise FileNotFoundError(f"No such file named {path}")  # noqa: TRY003

    entry = str(path)
    sys.path.insert(0, str(path.parent))

    from .core import SyncReloader

    _argv = sys.argv[:]
    sys.argv[:] = args
    _main = sys.modules["__main__"]
    try:
        reloader = SyncReloader(entry)
        sys.modules["__main__"] = mod = reloader.entry_module
        ns: dict = mod._ReactiveModule__namespace  # noqa: SLF001
        ns.update({"__package__": parent, "__spec__": None if parent is None else mod.__spec__})
        reloader.keep_watching_until_interrupt()
    finally:
        sys.argv[:] = _argv
        sys.modules["__main__"] = _main


def run_module(module_name: str, args: list[str]):
    if (cwd := str(Path.cwd())) not in sys.path:
        sys.path.insert(0, cwd)

    from importlib.util import find_spec

    from .core import ReactiveModule, SyncReloader, _loader, patch_meta_path

    patch_meta_path()

    spec = find_spec(module_name)
    if spec is None:
        raise ModuleNotFoundError(f"No module named '{module_name}'")  # noqa: TRY003

    if spec.submodule_search_locations is not None:
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

    args[0] = entry  # Replace the first argument with the full path

    _argv = sys.argv[:]
    sys.argv[:] = args
    _main = sys.modules["__main__"]
    try:
        reloader = SyncReloader(entry)
        if spec.loader is not _loader:
            spec.loader = _loader  # make it reactive
        namespace = {"__file__": entry, "__name__": "__main__", "__spec__": spec, "__loader__": _loader, "__package__": spec.parent, "__cached__": None, "__builtins__": builtins}
        sys.modules["__main__"] = reloader.entry_module = ReactiveModule(Path(entry), namespace, "__main__")
        reloader.keep_watching_until_interrupt()
    finally:
        sys.argv[:] = _argv
        sys.modules["__main__"] = _main

async def run_module_async(module_name: str, args: list[str]):
    if (cwd := str(Path.cwd())) not in sys.path:
        sys.path.insert(0, cwd)

    from importlib.util import find_spec

    from .core import ReactiveModule, AsyncReloader, _loader, patch_meta_path

    patch_meta_path()

    spec = find_spec(module_name)
    if spec is None:
        raise ModuleNotFoundError(f"No module named '{module_name}'")

    if spec.submodule_search_locations is not None:
        # It's a package, look for __main__.py
        spec = find_spec(f"{module_name}.__main__")
        if spec and spec.origin:
            entry = spec.origin
        else:
            raise ModuleNotFoundError(f"No module named '{module_name}.__main__'; '{module_name}' is a package and cannot be directly executed")
    elif spec.origin is None:
        raise ModuleNotFoundError(f"Cannot find entry point for module '{module_name}'")
    else:
        entry = spec.origin

    args.insert(0, entry)  # Replace the first argument with the full path

    _argv = sys.argv[:]
    sys.argv[:] = args
    _main = sys.modules["__main__"]
    try:
        reloader = AsyncReloader(entry)
        if spec.loader is not _loader:
            spec.loader = _loader  # make it reactive
        namespace = {"__file__": entry, "__name__": "__main__", "__spec__": spec, "__loader__": _loader, "__package__": spec.parent, "__cached__": None, "__builtins__": builtins}
        sys.modules["__main__"] = reloader.entry_module = ReactiveModule(Path(entry), namespace, "__main__")
        await reloader.keep_watching_until_interrupt()
    finally:
        sys.argv[:] = _argv
        sys.modules["__main__"] = _main


async def run_path_async(entry: str, args: list[str]):
    path = Path(entry).resolve()
    if path.is_dir():
        if (__main__ := path / "__main__.py").is_file():
            parent = ""
            path = __main__
        else:
            raise FileNotFoundError(f"No __main__.py file in {path}")
    elif path.is_file():
        parent = None
    else:
        raise FileNotFoundError(f"No such file named {path}")

    entry = str(path)
    sys.path.insert(0, str(path.parent))

    from .core import AsyncReloader

    _argv = sys.argv[:]
    sys.argv[:] = args
    _main = sys.modules["__main__"]
    try:
        reloader = AsyncReloader(entry)
        sys.modules["__main__"] = mod = reloader.entry_module
        ns: dict = mod._ReactiveModule__namespace
        ns.update({"__package__": parent, "__spec__": None if parent is None else mod.__spec__})
        await reloader.keep_watching_until_interrupt()
    finally:
        sys.argv[:] = _argv
        sys.modules["__main__"] = _main


def cli(args: list[str] | None = None):
    if args is None:
        args = sys.argv[1:]
    import asyncio
    from contextlib import suppress
    try:
        if len(args) < 1 or args[0] in ("--help", "-h"):
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

            # with suppress(SystemExit):
            asyncio.run(run_module_async(module_name, args[1:]))
        else:
            asyncio.run(run_path_async(args[0], args))
    except (FileNotFoundError, ModuleNotFoundError) as e:
        print(f"\n Error: {e}\n")
        return 1

    return 0


def main():
    sys.exit(cli(sys.argv[1:]))
