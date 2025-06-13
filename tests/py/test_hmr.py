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
    """
    Creates an isolated temporary environment for testing modules.
    
    This context manager sets up a temporary directory as the working directory, appends it to `sys.path`, captures standard output, and yields the captured output stream. Upon exit, it restores `sys.path` and `sys.modules` to their original states, ensuring test isolation.
    """
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
    """
    Context manager that waits for a hot module reload event to occur within a timeout.
    
    Yields control to the caller, then blocks until a reload event is triggered or the timeout elapses.
    """
    from threading import Event

    event = Event()

    with use_post_reload(event.set):
        try:
            yield
        finally:
            event.wait(timeout)


@asynccontextmanager
async def await_for_tick(timeout=1):
    """
    Asynchronous context manager that yields control and waits for a module reload event.
    
    Waits for a reload event to be triggered via `use_post_reload`, or until the specified timeout elapses.
    
    Args:
        timeout: Maximum time in seconds to wait for the reload event (default is 1).
    """
    from asyncio import Event, wait_for

    event = Event()

    with use_post_reload(event.set):
        try:
            yield
        finally:
            await wait_for(event.wait(), timeout)


async def test_reusing():
    """
    Tests reuse of synchronous and asynchronous reloader APIs, verifying that module reloads are triggered and output is captured correctly after file changes using both sync and async contexts.
    """
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
    """
    Tests that module-level __getattr__ is invoked on attribute access and that changes to __getattr__ trigger a reload.
    
    Verifies that printing an attribute from a module with __getattr__ produces the expected output, and that modifying __getattr__ updates the output after a reload.
    """
    with environment() as stdout:
        Path("foo.py").write_text("def __getattr__(name): print(name)")
        Path("main.py").write_text("import foo\nprint(foo.bar)")
        with SyncReloaderAPI("main.py"):
            assert stdout.delta == "bar\nNone\n"
            with wait_for_tick():
                Path("foo.py").write_text("def __getattr__(name): return name")
            assert stdout.delta == "bar\n"


async def test_simple_triggering():
    """
    Tests that modifying a dependency module triggers a reload and updates output.
    
    This test verifies that when a dependency ("bar.py") of a module ("foo.py") is changed, the hot module reloader detects the change, reloads the dependent module, and the output reflects the updated dependency.
    """
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
    """
    Tests that changes to a module's __getattr__ do not trigger redundant reloads if exported values remain unchanged.
    
    Verifies that reloads and output updates occur only when actual exported values change, not when only the implementation of __getattr__ is modified without affecting exports.
    """
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
    """
    Tests switching a module from explicit exports to only using __getattr__.
    
    Verifies that removing an explicitly exported variable and relying solely on
    __getattr__ changes the imported value after a hot reload.
    """
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
    """
    Tests hot module reloading behavior with circular dependencies among modules.
    
    Creates three modules ("a.py", "b.py", "c.py") with circular imports and verifies
    the order and output of reloads after modifying each module. Asserts that reloads
    propagate through the dependency chain and that output reflects updated values.
    Includes comments on suboptimal reload order and possible improvements.
    """
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
    """
    Tests that private methods in a module are not accessible for import.
    
    Verifies that attempting to import a private method (such as 'load') from a module under hot module reloading raises an ImportError.
    """
    with environment():
        Path("main.py").touch()
        with SyncReloaderAPI("main.py"), pytest.raises(ImportError):
            exec("from main import load")


def test_reload_from_outside():
    """
    Tests manual reloading of a ReactiveModule instance using the load utility.
    
    Verifies that calling load on a ReactiveModule triggers module execution and output, and that repeated calls without changes do not produce additional output. Also checks that calling the module's load method directly raises an AttributeError.
    """
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
    """
    Tests that `inspect.getsourcefile` returns the correct filename for a class defined in a reloaded module.
    """
    with environment() as stdout:
        Path("main.py").write_text("from inspect import getsourcefile\n\nclass Foo: ...\n\nprint(getsourcefile(Foo))")
        with SyncReloaderAPI("main.py"):
            assert stdout == "main.py\n"


def test_using_reactivity_under_hmr():
    """
    Tests integration of reactivity primitives with hot module reloading.
    
    Verifies that signals and effects from the `reactivity` library function correctly within a reloaded module, ensuring reactive updates propagate as expected after reloads.
    """
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
    """
    Tests that the `cache_across_reloads` decorator preserves function results across module reloads.
    
    Verifies that output is only produced when the function's dependencies or logic change, and not on redundant reloads.
    """
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


@pytest.mark.xfail(raises=NameError, strict=True)
def test_cache_across_reloads_with_class():
    """
    Tests that using cache_across_reloads with a function defining a class referencing an external variable triggers correct output and error handling.
    
    This test writes a function decorated with cache_across_reloads that defines a class referencing a variable 'a', loads the module, and asserts the expected output.
    """
    with environment() as stdout:
        Path("main.py").write_text("from reactivity.hmr import cache_across_reloads\n\n@cache_across_reloads\ndef f():\n    class _:\n        print(a)\n\nf()\n")
        load(ReactiveModule(Path("main.py"), {"a": 1}, "main"))
        assert stdout.delta == "1\n"
