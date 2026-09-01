from collections.abc import Callable
from contextlib import contextmanager
from importlib import import_module
from inspect import isgeneratorfunction, unwrap
from pathlib import Path
from typing import Any

from pytest import MonkeyPatch, WarningsRecorder


@contextmanager
def recwarn():
    from warnings import simplefilter

    with WarningsRecorder() as wrec:
        simplefilter("default")
        yield wrec


@contextmanager
def monkeypatch():
    mpatch = MonkeyPatch()
    try:
        yield mpatch
    finally:
        mpatch.undo()


builtin_fixtures = {"monkeypatch": monkeypatch, "recwarn": recwarn}


def find_fixtures(path: Path) -> dict[str, Callable[[], Any]]:
    fixtures: dict[str, Callable[[], Any]] = {}

    for file_path in *path.rglob("conftest.py"), *path.rglob("test_*.py"), *path.rglob("*_test.py"):
        # Skip venv and site-packages directories
        if ".venv" in file_path.parts or "site-packages" in file_path.parts:
            continue
        rel_path = file_path.relative_to(path)
        module_name = rel_path.with_suffix("").as_posix().replace("/", ".")

        ns = import_module(module_name).__dict__

        for name, obj in ns.items():
            if hasattr(obj, "_fixture_function_marker"):  # @pytest.fixture marker
                function = unwrap(obj)
                if isgeneratorfunction(function):
                    function = contextmanager(function)
                fixtures[name] = function

    return builtin_fixtures | fixtures
