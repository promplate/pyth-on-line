from contextlib import asynccontextmanager, contextmanager
from inspect import getsource
from pathlib import Path

import pytest
from reactivity.hmr.api import AsyncReloaderAPI, SyncReloaderAPI
from reactivity.hmr.core import ReactiveModule
from reactivity.hmr.hooks import use_post_reload
from reactivity.hmr.utils import load
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
        api = SyncReloaderAPI("main.py")
        with SyncReloaderAPI("main.py"):
            assert env.stdout_delta == "1\n"
            # can't wait / await here
            # this is weird because we actually can do it in the next test
            # so maybe somehow the first test act as a warm-up of something
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


def test_module_getattr():
    with environment() as env:
        env["foo.py"] = "def __getattr__(name): print(name)"
        env["main.py"] = "import foo\nprint(foo.bar)"
        with env.hmr("main.py"):
            assert env.stdout_delta == "bar\nNone\n"
            env["foo.py"] = "def __getattr__(name): return name"
            assert env.stdout_delta == "bar\n"


def test_simple_triggering():
    with environment() as env:
        env["foo.py"] = "from bar import baz\nprint(baz())"
        env["bar.py"] = "def baz(): return 1"
        with env.hmr("foo.py"):
            assert env.stdout_delta == "1\n"
            env["bar.py"] = "def baz(): return 2"
            assert env.stdout_delta == "2\n"


def test_getattr_no_redundant_trigger():
    with environment() as env:
        env["foo.py"] = "a = 123\ndef __getattr__(name): return name"
        env["main.py"] = "from foo import a\nprint(a)"
        with env.hmr("main.py"):
            assert env.stdout_delta == "123\n"

            env["foo.py"].replace("return name", "return name * 2")
            assert env.stdout_delta == ""

            env["foo.py"] = "a = 234"
            assert env.stdout_delta == "234\n"

            env["main.py"].replace("a", "b")
            assert env.stdout_delta == "bb\n"

            env["foo.py"] = "def __getattr__(name): return name * 4"
            assert env.stdout_delta == "bbbb\n"


@pytest.mark.xfail(raises=AssertionError, strict=True)
def test_switch_to_getattr():
    with environment() as env:
        env["foo.py"] = "a = 123\ndef __getattr__(name): return name"
        env["main.py"] = "from foo import a\nprint(a)"
        with env.hmr("main.py"):
            assert env.stdout_delta == "123\n"

            env["foo.py"].replace("a = 123", "")
            assert env.stdout_delta == "a\n"


def test_simple_circular_dependency():
    with environment() as env:
        env["a.py"] = "print('a')\n\none = 1\n\nfrom b import two\n\nthree = two + 1\n"
        env["b.py"] = "print('b')\n\nfrom a import one\n\ntwo = one + 1\n"
        env["c.py"] = "print('c')\n\nfrom a import three\n\nprint(three)\n"

        with env.hmr("c.py"):
            assert env.stdout_delta == "c\na\nb\n3\n"  # c -> a -> b

            env["a.py"].replace("three = two + 1", "three = two + 2")
            assert env.stdout_delta == "a\nc\n4\n"  # a <- c

            env["b.py"].replace("two = one + 1", "two = one + 2")
            assert env.stdout_delta == "b\na\nc\n5\n"  # b <- a <- c

            env["a.py"].replace("one = 1", "one = 2")
            assert env.stdout_delta == "a\nb\na\nc\n6\n"  # a <- b, b <- a <- c

            """
              TODO This is not an optimal behavior. Here are 2 alternate solutions:

                1. Maximize consistency:
                   Log the order of each `Derived` and replay every loop in its original order.
                   Always run `a` before `b` in the tests above.
                2. Greedy memoization:
                   Always run the changed module first. Only run `a` when necessary.
                   But if `a.one` changes every time, we'll have to run `b` twice to keep consistency.
            """


def test_private_methods_inaccessible():
    with environment() as env:
        env["main.py"].touch()
        with env.hmr("main.py"):
            with pytest.raises(ImportError):
                exec("from main import load")
            with pytest.raises(ImportError):
                exec("from main import instances")


def test_reload_from_outside():
    with environment() as env:
        env["main.py"] = "print(123)"
        file = Path("main.py")
        module = ReactiveModule(file, {}, "main")
        assert env.stdout_delta == ""

        with pytest.raises(AttributeError):
            module.load()

        load(module)
        assert env.stdout_delta == "123\n"

        load(module)
        assert env.stdout_delta == ""


def test_getsourcefile():
    with environment() as env:
        env["main.py"] = "from inspect import getsourcefile\n\nclass Foo: ...\n\nprint(getsourcefile(Foo))"
        with env.hmr("main.py"):
            assert env.stdout_delta == "main.py\n"


def test_using_reactivity_under_hmr():
    with environment() as env:

        def simple_test():
            from reactivity import create_effect, create_signal
            from utils import capture_stdout

            get_s, set_s = create_signal(0)

            with capture_stdout() as stdout, create_effect(lambda: print(get_s())):
                assert stdout.delta == "0\n"
                set_s(1)
                assert stdout.delta == "1\n"

        simple_test()

        source = f"{getsource(simple_test)}\n\n{simple_test.__name__}()"

        env["main.py"].touch()

        with env.hmr("main.py"):
            env["main.py"] = source

        assert env.stdout_delta == ""


def test_cache_across_reloads():
    with environment() as env:
        env["main.py"] = """
        from reactivity.hmr import cache_across_reloads

        a = 1

        @cache_across_reloads
        def f():
            print(a + 1)

        f()
        """

        with env.hmr("main.py"):
            assert env.stdout_delta == "2\n"
            env["main.py"].touch()
            assert env.stdout_delta == ""
            env["main.py"].replace("a = 1", "a = 2")
            assert env.stdout_delta == "3\n"
            env["main.py"].replace("a + 1", "a + 2")
            assert env.stdout_delta == "4\n"


def test_cache_across_reloads_with_class():
    with environment() as env:
        env["main.py"] = "from reactivity.hmr import cache_across_reloads\n\n@cache_across_reloads\ndef f():\n    class _:\n        print(a)\n\nf()\n"
        load(ReactiveModule(Path("main.py"), {"a": 1}, "main"))
        assert env.stdout_delta == "1\n"


def test_cache_across_reloads_source():
    with environment() as env:
        env["main.py"] = """
                from inspect import getsource
                from reactivity.hmr.utils import cache_across_reloads

                def f(): pass

                assert getsource(f) == getsource(cache_across_reloads(f))
            """
        load(ReactiveModule(Path("main.py"), {}, "main"))


def test_cache_across_reloads_with_other_decorators():
    with environment() as env:
        env["main.py"] = """
                from reactivity.hmr.utils import cache_across_reloads

                @lambda f: [print(1), f()][1]
                @cache_across_reloads
                @lambda f: print(3) or f
                def two(): return 2
            """
        load(ReactiveModule(Path("main.py"), ns := {}, "main"))
        assert env.stdout_delta == "3\n3\n1\n"  # inner function being called twice, while the outer one only once
        assert ns["two"] == 2
