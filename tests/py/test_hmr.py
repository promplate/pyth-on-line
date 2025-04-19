import sys
from contextlib import asynccontextmanager, chdir, contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from utils import capture_stdout

from src.python.common.reactivity.hmr.api import AsyncReloaderAPI, SyncReloaderAPI
from src.python.common.reactivity.hmr.hooks import use_post_reload


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


@contextmanager
def wait_for_tick(timeout=1):
    from threading import Event

    event = Event()

    with use_post_reload(event.set):
        try:
            yield
        finally:
            event.wait(timeout)


@asynccontextmanager
async def await_for_tick(timeout=1):
    from asyncio import Event, wait_for

    event = Event()

    with use_post_reload(event.set):
        try:
            yield
        finally:
            await wait_for(event.wait(), timeout)


async def test_reusing():
    with environment() as stdout:
        Path("main.py").write_text("print(1)")
        api = SyncReloaderAPI("main.py")
        with SyncReloaderAPI("main.py"):
            assert stdout.delta == "1\n"
            # can't wait / await here
            # this is weird because we actually can do it in the next test
            # so maybe somehow the first test act as a warm-up of something
        with api:
            assert stdout.delta == "1\n"
            with wait_for_tick():
                Path("main.py").write_text("print(1)")
            assert stdout.delta == "1\n"
            async with await_for_tick():
                Path("main.py").write_text("print(1)")
            assert stdout.delta == "1\n"
        async with api:
            assert stdout.delta == "1\n"
            with wait_for_tick():
                Path("main.py").write_text("print(1)")
            assert stdout.delta == "1\n"
            async with await_for_tick():
                Path("main.py").write_text("print(1)")
            assert stdout.delta == "1\n"

    with environment() as stdout:
        Path("main.py").write_text("print(2)")
        api = AsyncReloaderAPI("main.py")
        with api:
            assert stdout.delta == "2\n"
            with wait_for_tick():
                Path("main.py").write_text("print(2)")
            assert stdout.delta == "2\n"
            async with await_for_tick():
                Path("main.py").write_text("print(2)")
            assert stdout.delta == "2\n"
        async with api:
            assert stdout.delta == "2\n"
            # can't wait here too
            # even more weird
            # but this time repeating this block won't work
            async with await_for_tick():
                Path("main.py").write_text("print(2)")
            assert stdout.delta == "2\n"


def test_module_getattr():
    with environment() as stdout:
        Path("foo.py").write_text("def __getattr__(name): print(name)")
        Path("main.py").write_text("import foo\nprint(foo.bar)")
        with SyncReloaderAPI("main.py"):
            assert stdout.delta == "bar\nNone\n"
            with wait_for_tick():
                Path("foo.py").write_text("def __getattr__(name): return name")
            assert stdout.delta == "bar\n"


async def test_simple_triggering():
    with environment() as stdout:
        foo = Path("foo.py")
        bar = Path("bar.py")
        foo.write_text("from bar import baz\nprint(baz())")
        bar.write_text("def baz(): return 1")
        async with AsyncReloaderAPI("foo.py"):
            assert stdout.delta == "1\n"
            async with await_for_tick():
                bar.write_text("def baz(): return 2")
            assert stdout.delta == "2\n"
