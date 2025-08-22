"""Command-line interface for HMR (Hot Module Reload)."""

import sys
from pathlib import Path

from .core import SyncReloader


def parse_arguments() -> tuple[str, bool]:
    """Parse command line arguments and return entry point and module flag.

    Returns:
        tuple: (entry_point, is_module_mode)
    """
    if len(sys.argv) < 2:
        print("\n Usage: hmr <entry file>, just like python <entry file>")
        print(" Usage: hmr -m <module>, just like python -m <module>\n")
        exit(1)

    sys.argv.pop(0)  # Remove script name

    # Check for -m flag
    if sys.argv[0] == "-m":
        if len(sys.argv) < 2:
            print("\n Usage: hmr -m <module>, just like python -m <module>\n")
            exit(1)

        module_name = sys.argv[1]
        sys.argv.pop(0)  # Remove -m flag
        return module_name, True
    else:
        return sys.argv[0], False


def resolve_module(module_name: str) -> str:
    """Resolve a module name to its file path.

    Args:
        module_name: Name of the module to resolve

    Returns:
        str: Path to the module file

    Raises:
        SystemExit: If module cannot be found or resolved
    """
    # Add current directory to sys.path if not already there
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

        return entry

    except ModuleNotFoundError as e:
        print(f"Error: {e}")
        exit(1)


def resolve_file(file_path: str) -> str:
    """Resolve a file path and validate it exists.

    Args:
        file_path: Path to the file

    Returns:
        str: Validated file path

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(path.resolve())

    # Add parent directory to sys.path
    sys.path.insert(0, str(path.parent.resolve()))
    return file_path


def cli():
    """Main entry point for HMR CLI."""
    # Parse command line arguments
    entry_arg, is_module_mode = parse_arguments()

    # Resolve entry point based on mode
    if is_module_mode:
        entry = resolve_module(entry_arg)
        sys.argv[0] = entry
    else:
        entry = resolve_file(entry_arg)

    # Create and run the reloader
    reloader = SyncReloader(entry)
    sys.modules["__main__"] = reloader.entry_module
    reloader.keep_watching_until_interrupt()
