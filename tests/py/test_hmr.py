import sys
from contextlib import chdir, contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from utils import capture_stdout

from src.python.common.reactivity.hmr.api import AsyncReloaderAPI, SyncReloaderAPI


@contextmanager
def environment():
    with TemporaryDirectory() as tmpdir, chdir(tmpdir), capture_stdout() as stdout:
        sys.path.append(tmpdir)
        modules = sys.modules.copy()
        try:
            yield stdout
        finally:
            sys.path.remove(tmpdir)
            sys.modules = modules


async def test_reusing():
    with environment() as stdout:
        Path("main.py").write_text("print(1)")
        api = SyncReloaderAPI("main.py")
        with api:
            assert stdout == "1\n"
        async with api:
            assert stdout == "1\n1\n"

    with environment() as stdout:
        Path("main.py").write_text("print(2)")
        api = AsyncReloaderAPI("main.py")
        with api:
            assert stdout == "2\n"
        async with api:
            assert stdout == "2\n2\n"


@pytest.mark.xfail(strict=True)
def test_module_getattr():
    with environment() as stdout:
        Path("foo.py").write_text("def __getattr__(name): print(name)")
        Path("main.py").write_text("import foo\nprint(foo.bar)")
        with SyncReloaderAPI("main.py"):
            assert stdout == "bar\nNone\n"
