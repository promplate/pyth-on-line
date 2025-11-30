from collections.abc import Callable
from pathlib import Path
from runpy import run_path
from typing import Any


def find_test_root(dir_path: Path):
    """Find the root directory containing test files, like pytest does."""
    for test_file in dir_path.rglob("test_*.py"):
        return test_file.parent
    for test_file in dir_path.rglob("*_test.py"):
        return test_file.parent
    return dir_path


def find_test_functions(root_dir: Path):
    """Find all test functions in test files, mimicking pytest's discovery logic."""
    test_functions: list[Callable[..., Any]] = []

    for file in *root_dir.rglob("test_*.py"), *root_dir.rglob("*_test.py"):
        # Compute module name from relative path
        module_name = file.relative_to(root_dir).with_suffix("").as_posix().replace("/", ".")

        # Execute the test file and get its globals namespace
        ns = run_path(str(file), None, module_name)

        # Traverse the namespace dict produced by run_path
        for name, obj in ns.items():
            if callable(obj) and name.startswith("test"):
                test_functions.append(obj)
            elif isinstance(obj, type) and name.startswith("Test"):
                # For test classes, traverse their methods
                for method_name in dir(obj):
                    if method_name.startswith("test"):
                        method = getattr(obj, method_name)
                        if callable(method):
                            test_functions.append(method)

    return test_functions
