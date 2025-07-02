import sys
from contextlib import asynccontextmanager, chdir, contextmanager
from inspect import getsource
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

import pytest
from reactivity.hmr.api import AsyncReloaderAPI, SyncReloaderAPI
from reactivity.hmr.core import ReactiveModule
from reactivity.hmr.hooks import use_post_reload
from reactivity.hmr.utils import load
from utils import capture_stdout


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


async def test_getattr_no_redundant_trigger():
    with environment() as stdout:
        foo = Path("foo.py")
        main = Path("main.py")
        foo.write_text("a = 123\ndef __getattr__(name): return name")
        main.write_text("from foo import a\nprint(a)")
        async with AsyncReloaderAPI("main.py"):
            assert stdout.delta == "123\n"

            async with await_for_tick():
                foo.write_text("a = 123\ndef __getattr__(name): return name * 2")
            assert stdout.delta == ""

            async with await_for_tick():
                foo.write_text("a = 234")
            assert stdout.delta == "234\n"

            async with await_for_tick():
                main.write_text("from foo import b\nprint(b)")
            assert stdout.delta == "bb\n"

            async with await_for_tick():
                foo.write_text("def __getattr__(name): return name * 4")
            assert stdout.delta == "bbbb\n"


@pytest.mark.xfail(raises=AssertionError, strict=True)
async def test_switch_to_getattr():
    with environment() as stdout:
        foo = Path("foo.py")
        main = Path("main.py")
        foo.write_text("a = 123\ndef __getattr__(name): return name")
        main.write_text("from foo import a\nprint(a)")
        async with AsyncReloaderAPI("main.py"):
            assert stdout.delta == "123\n"

            async with await_for_tick():
                foo.write_text("def __getattr__(name): return name")
            assert stdout.delta == "a\n"


def test_simple_circular_dependency():
    with environment() as stdout:
        Path("a.py").write_text("print('a')\n\none = 1\n\nfrom b import two\n\nthree = two + 1\n")
        Path("b.py").write_text("print('b')\n\nfrom a import one\n\ntwo = one + 1\n")
        Path("c.py").write_text("print('c')\n\nfrom a import three\n\nprint(three)\n")

        with SyncReloaderAPI("c.py"):
            assert stdout.delta == "c\na\nb\n3\n"  # c -> a -> b

            with wait_for_tick():
                Path("a.py").write_text("print('a')\n\none = 1\n\nfrom b import two\n\nthree = two + 2\n")
            assert stdout.delta == "a\nc\n4\n"  # a <- c

            with wait_for_tick():
                Path("b.py").write_text("print('b')\n\nfrom a import one\n\ntwo = one + 2\n")
            assert stdout.delta == "b\na\nc\n5\n"  # b <- a <- c

            with wait_for_tick():
                Path("a.py").write_text("print('a')\n\none = 2\n\nfrom b import two\n\nthree = two + 2\n")
            assert stdout.delta == "a\nb\na\nc\n6\n"  # a <- b, b <- a <- c

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
    with environment():
        Path("main.py").touch()
        with SyncReloaderAPI("main.py"):
            with pytest.raises(ImportError):
                exec("from main import load")
            with pytest.raises(ImportError):
                exec("from main import instances")


def test_reload_from_outside():
    with environment() as stdout:
        file = Path("main.py")
        file.write_text("print(123)")
        module = ReactiveModule(file, {}, "main")
        assert stdout == ""

        with pytest.raises(AttributeError):
            module.load()

        load(module)
        assert stdout.delta == "123\n"

        load(module)
        assert stdout.delta == ""


def test_getsourcefile():
    with environment() as stdout:
        Path("main.py").write_text("from inspect import getsourcefile\n\nclass Foo: ...\n\nprint(getsourcefile(Foo))")
        with SyncReloaderAPI("main.py"):
            assert stdout == "main.py\n"


def test_using_reactivity_under_hmr():
    with environment() as stdout:

        def simple_test():
            from reactivity import create_effect, create_signal
            from utils import capture_stdout

            get_s, set_s = create_signal(0)

            with capture_stdout() as stdout, create_effect(lambda: print(get_s())):
                assert stdout.delta == "0\n"
                set_s(1)
                assert stdout.delta == "1\n"

        simple_test()

        source = f"{dedent(getsource(simple_test))}\n\n{simple_test.__name__}()"

        Path("main.py").touch()

        with SyncReloaderAPI("main.py"), wait_for_tick():
            Path("main.py").write_text(source)

        assert stdout == "", stdout


def test_cache_across_reloads():
    with environment() as stdout:
        file = Path("main.py")
        file.write_text(
            source := dedent(
                """

        from reactivity.hmr import cache_across_reloads

        a = 1

        @cache_across_reloads
        def f():
            print(a + 1)

        f()

            """
            )
        )

        Path("main.py").write_text(source)

        with SyncReloaderAPI("main.py"):
            assert stdout.delta == "2\n"
            with wait_for_tick():
                Path("main.py").write_text(source)
            assert stdout.delta == ""
            with wait_for_tick():
                Path("main.py").write_text(source := source.replace("a = 1", "a = 2"))
            assert stdout.delta == "3\n"
            with wait_for_tick():
                Path("main.py").write_text(source := source.replace("a + 1", "a + 2"))
            assert stdout.delta == "4\n"


def test_cache_across_reloads_with_class():
    with environment() as stdout:
        Path("main.py").write_text("from reactivity.hmr import cache_across_reloads\n\n@cache_across_reloads\ndef f():\n    class _:\n        print(a)\n\nf()\n")
        load(ReactiveModule(Path("main.py"), {"a": 1}, "main"))
        assert stdout.delta == "1\n"


def test_cache_across_reloads_source():
    with environment():
        Path("main.py").write_text(
            dedent(
                """

                from inspect import getsource
                from reactivity.hmr.utils import cache_across_reloads

                def f(): pass

                assert getsource(f) == getsource(cache_across_reloads(f))

                """
            )
        )
        load(ReactiveModule(Path("main.py"), {}, "main"))


def test_cache_across_reloads_with_other_decorators():
    with environment() as stdout:
        Path("main.py").write_text(
            dedent(
                """

                from reactivity.hmr.utils import cache_across_reloads

                @lambda f: [print(1), f()][1]
                @cache_across_reloads
                @lambda f: print(3) or f
                def two(): return 2

                """
            )
        )
        load(ReactiveModule(Path("main.py"), ns := {}, "main"))
        assert stdout.delta == "3\n3\n1\n"  # inner function being called twice, while the outer one only once
        assert ns["two"] == 2
