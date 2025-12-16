from contextlib import asynccontextmanager, contextmanager

from reactivity.hmr.api import AsyncReloaderAPI, SyncReloaderAPI
from reactivity.hmr.hooks import use_post_reload
from utils import environment


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
    with environment() as env:
        env["main.py"] = "print(1)"
        with SyncReloaderAPI("main.py") as api:
            assert env.stdout_delta == "1\n"
            # can't wait / await here
            # this is weird because we actually can do it in the next test
            # so maybe somehow the first test act as a warm-up of something
            api.dispose()
        api = SyncReloaderAPI("main.py")
        with api:
            assert env.stdout_delta == "1\n"
            with wait_for_tick():
                env["main.py"].touch()
            assert env.stdout_delta == "1\n"
            async with await_for_tick():
                env["main.py"].touch()
            assert env.stdout_delta == "1\n"
        async with api:
            assert env.stdout_delta == "1\n"
            with wait_for_tick():
                env["main.py"].touch()
            assert env.stdout_delta == "1\n"
            async with await_for_tick():
                env["main.py"].touch()
            assert env.stdout_delta == "1\n"
        api.dispose()

    with environment() as env:
        env["main.py"] = "print(2)"
        api = AsyncReloaderAPI("main.py")
        with api:
            assert env.stdout_delta == "2\n"
            with wait_for_tick():
                env["main.py"].touch()
            assert env.stdout_delta == "2\n"
            async with await_for_tick():
                env["main.py"].touch()
            assert env.stdout_delta == "2\n"
        async with api:
            assert env.stdout_delta == "2\n"
            # can't wait here too
            # even more weird
            # but this time repeating this block won't work
            async with await_for_tick():
                env["main.py"].touch()
            assert env.stdout_delta == "2\n"
        api.dispose()


def test_module_getattr():
    with environment() as env:
        env["foo.py"] = "def __getattr__(name): print(name)"
        env["main.py"] = "import foo\nprint(foo.bar)"
        with env.hmr("main.py"):
            assert env.stdout_delta == "bar\nNone\n"
            env["foo.py"].replace("print(name)", "return name")
            assert env.stdout_delta == "bar\n"
