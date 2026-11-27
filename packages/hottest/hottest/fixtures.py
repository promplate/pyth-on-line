from collections.abc import Callable
from contextlib import contextmanager
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from inspect import isgeneratorfunction, unwrap
from pathlib import Path
from sys import modules
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

        from ._vendored_reactivity.hmr.core import ReactiveModule, _loader
        from ._vendored_reactivity.hmr.fs import track
        from ._vendored_reactivity.hmr.utils import load

        if file_path.name == "conftest.py":
            track(file_path.resolve())
        if file_path.name == "conftest.py" and module_name not in modules:
            spec = spec_from_file_location(module_name, file_path, loader=_loader)
            assert spec is not None
            module = module_from_spec(spec)
            modules[module_name] = module
        module = import_module(module_name)
        if isinstance(module, ReactiveModule):
            load(module)
        ns = vars(module)

        for name, obj in ns.items():
            if hasattr(obj, "_fixture_function_marker"):  # @pytest.fixture marker
                function = unwrap(obj)
                if isgeneratorfunction(function):
                    function = contextmanager(function)
                fixtures[name] = function

    return builtin_fixtures | fixtures
