from importlib import import_module
from inspect import getsource
from pathlib import Path
from textwrap import dedent

import pytest
from reactivity.hmr.core import ReactiveModule
from reactivity.hmr.utils import load
from utils import environment


def test_simple_triggering():
    with environment() as env:
        env["foo.py"] = "from bar import baz\nprint(baz())"
        env["bar.py"] = "def baz(): return 1"
        with env.hmr("foo.py"):
            assert env.stdout_delta == "1\n"
            env["bar.py"].replace("1", "2")
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

        source = f"{dedent(getsource(simple_test))}\n\n{simple_test.__name__}()"

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


def test_cache_across_reloads_cache_lifespan():
    with environment() as env:
        env["main.py"] = """
            from reactivity.hmr import cache_across_reloads

            @cache_across_reloads
            def f():
                print(1)

            f()
        """
        with env.hmr("main.py"):
            assert env.stdout_delta == "1\n"
            env["main.py"].replace("1", "2")
            assert env.stdout_delta == "2\n"
            env["main.py"].replace("2", "1")
            assert env.stdout_delta == "1\n"


def test_cache_across_reloads_same_sources():
    with environment() as env:
        env["a.py"] = env["b.py"] = """
            from reactivity.hmr import cache_across_reloads

            value = 1

            @cache_across_reloads
            def f():
                print(value)

            f()

        """
        env["main.py"] = "import a, b; a.f(); b.f()"
        with env.hmr("main.py"):
            assert env.stdout_delta == "1\n1\n"
            env["a.py"].replace("value = 1", "value = 2")
            assert env.stdout_delta == "2\n"
            env["b.py"].replace("value = 1", "value = 3")
            assert env.stdout_delta == "3\n"


def test_cache_across_reloads_chaining():
    with environment() as env:
        env["foo.py"] = """
            from reactivity.hmr import cache_across_reloads

            @cache_across_reloads
            def f():
                print(1)
                return 1
        """
        env["main.py"] = """
            from reactivity.hmr import cache_across_reloads

            from foo import f

            value = 123

            @cache_across_reloads
            def g():
                f()
                print(value)

            g()
        """

        with env.hmr("main.py"):
            assert env.stdout_delta == "1\n123\n"
            env["foo.py"].replace("1", "2")
            assert env.stdout_delta == "2\n123\n"
            env["main.py"].replace("123", "234")
            assert env.stdout_delta == "234\n"
            env["foo.py"].touch()
            env["main.py"].touch()
            assert env.stdout_delta == ""
            env["foo.py"].replace("print(2)", "print(3)")
            assert env.stdout_delta == "3\n"  # return value don't change, so no need to re-run `g()`


def test_cache_across_reloads_traceback():
    with environment() as env:
        env["main.py"] = """
            from sys import stdout
            from traceback import print_exc
            from reactivity.hmr.utils import cache_across_reloads

            def main():
                @cache_across_reloads
                def f():
                    try:
                        _ = 1 / 0
                    except:
                        print_exc(limit=1, file=stdout)
                f()
            main()
        """

        expected_segment = "    _ = 1 / 0\n        ~~^~~"
        with env.hmr("main.py"):
            assert expected_segment in env.stdout_delta
            env["main.py"].touch()
            assert env.stdout_delta == ""
            env["main.py"].replace("1 / 0", "2 / 0")
            assert expected_segment.replace("1", "2") in env.stdout_delta


def test_module_metadata():
    with environment() as env:
        env["main.py"] = "'abc'; print(__doc__)"
        with env.hmr("main.py"):
            assert env.stdout_delta == "abc\n"
            assert import_module("main").__builtins__ is __builtins__

            env["a/b/__init__.py"].touch()
            env["a/b/c/d.py"].touch()
            env["a/b/e.py"].touch()

            assert import_module("a.b.c.d").__package__ == "a.b.c"
            assert import_module("a.b.c").__package__ == "a.b.c"
            assert import_module("a.b.e").__package__ == "a.b"
            assert import_module("a.b").__package__ == "a.b"


def test_search_paths_caching(monkeypatch: pytest.MonkeyPatch):
    with environment() as env:
        env["main.py"] = ""
        env["foo/bar.py"] = "print()"
        with env.hmr("main.py"):
            with pytest.raises(ModuleNotFoundError):
                env["main.py"] = "import bar"
            monkeypatch.syspath_prepend("foo")
            env["main.py"].touch()
            assert env.stdout_delta == "\n"
            assert isinstance(import_module("bar"), ReactiveModule)


def test_fs_signals():
    with environment() as env:
        env["main.py"] = "print(open('a').read())"
        env["a"] = "1"

        with env.hmr("main.py"):
            assert env.stdout_delta == "1\n"
            env["a"] = "2"
            assert env.stdout_delta == "2\n"
            with pytest.raises(FileNotFoundError):
                env["main.py"].replace("'a'", "'b'")
            env["a"] = "3"
            assert env.stdout_delta == ""
            env["b"] = "4"
            assert env.stdout_delta == "4\n"
            env["b"].touch()
            assert env.stdout_delta == "4\n"


def test_module_global_writeback():
    with environment() as env:
        env["main.py"] = "def f():\n    global x\n    x = 123\n\nf()"
        with env.hmr("main.py"):
            assert import_module("main").x == 123


def test_laziness():
    with environment() as env:
        env["foo.py"] = "bar = 1; print(bar)"
        env["main.py"] = "from foo import bar"
        with env.hmr("main.py"):
            env["foo.py"].replace("1", "2")
            assert env.stdout_delta == "1\n2\n"
            env["main.py"] = ""
            env["foo.py"].replace("2", "3")
            assert env.stdout_delta == ""
            env["main.py"] = "from foo import bar"
            assert env.stdout_delta == "3\n"
            env["foo.py"].touch()
            assert env.stdout_delta == "3\n"


def test_usersitepackages_none(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("site.USER_SITE", None)
    monkeypatch.setattr("site.getuserbase", lambda: None)
    with environment() as env:
        env["main.py"] = "print('hello')"
        with env.hmr("main.py"):
            assert env.stdout_delta == "hello\n"


def test_deep_imports():
    with environment() as env:
        env["main.py"] = "from foo.bar import baz"
        env["foo/bar.py"] = "print(baz := 123)"
        with env.hmr("main.py"):
            assert env.stdout_delta == "123\n"
            env["foo/bar.py"].replace("123", "234")
            assert env.stdout_delta == "234\n"


def test_cache_across_reloads_gc_function_removal():
    """Test that memos are garbage collected when functions are completely removed."""
    from reactivity.hmr.utils import functions, memos

    # Clear any existing state
    memos.clear()
    functions.clear()

    with environment() as env:
        env["main.py"] = """
        from reactivity.hmr import cache_across_reloads

        @cache_across_reloads
        def f():
            print("f called")
            return "f"

        @cache_across_reloads
        def g():
            print("g called")
            return "g"

        f()
        g()
        """

        with env.hmr("main.py"):
            assert env.stdout_delta == "f called\ng called\n"

            # After initial execution, both functions should be in memos and functions
            assert len(memos) == 2
            assert len(functions) == 2

            # Remove function f but keep g, add a new function h
            env["main.py"] = """
        from reactivity.hmr import cache_across_reloads

        @cache_across_reloads
        def g():
            print("g called")
            return "g"

        @cache_across_reloads
        def h():
            print("h called")
            return "h"

        g()
        h()
        """

            assert env.stdout_delta == "h called\n"

            # After reload, memo for f should be garbage collected
            # Only g and h should remain in both memos and functions
            assert len(memos) == 2
            assert len(functions) == 2

            # Verify the specific functions
            function_names = {key[1] for key in functions}
            memo_names = {key[1] for key in memos}
            assert function_names == {"g", "h"}
            assert memo_names == {"g", "h"}


def test_cache_across_reloads_gc_function_modification():
    """Test that memos persist when functions are modified but not removed."""
    from reactivity.hmr.utils import functions, memos

    # Clear any existing state
    memos.clear()
    functions.clear()

    with environment() as env:
        env["main.py"] = """
        from reactivity.hmr import cache_across_reloads

        @cache_across_reloads
        def f():
            print("original f")
            return "original"

        f()
        """

        with env.hmr("main.py"):
            assert env.stdout_delta == "original f\n"

            # After initial execution, function should be in both dicts
            assert len(memos) == 1
            assert len(functions) == 1
            original_memo_key = next(iter(memos.keys()))

            # Modify the function content but keep the same name
            env["main.py"].replace("original f", "modified f")

            assert env.stdout_delta == "modified f\n"

            # After modification, the function should still be in both dicts
            # The memo should persist (same key) but be invalidated/updated
            assert len(memos) == 1
            assert len(functions) == 1
            current_memo_key = next(iter(memos.keys()))
            assert current_memo_key == original_memo_key  # Same key (path, qualname)


def test_cache_across_reloads_gc_selective_removal():
    """Test selective gc when some functions are removed but others remain."""
    from reactivity.hmr.utils import functions, memos

    # Clear any existing state
    memos.clear()
    functions.clear()

    with environment() as env:
        env["main.py"] = """
        from reactivity.hmr import cache_across_reloads

        @cache_across_reloads
        def func_a():
            print("a")
            return "a"

        @cache_across_reloads
        def func_b():
            print("b")
            return "b"

        @cache_across_reloads
        def func_c():
            print("c")
            return "c"

        func_a()
        func_b()
        func_c()
        """

        with env.hmr("main.py"):
            assert env.stdout_delta == "a\nb\nc\n"

            # All three functions should be present
            assert len(memos) == 3
            assert len(functions) == 3

            # Remove func_a and func_c, keep only func_b
            env["main.py"] = """
        from reactivity.hmr import cache_across_reloads

        @cache_across_reloads
        def func_b():
            print("b modified")
            return "b"

        func_b()
        """

            assert env.stdout_delta == "b modified\n"

            # After reload, only func_b should remain in both dicts
            assert len(memos) == 1
            assert len(functions) == 1

            remaining_function = next(iter(functions.keys()))[1]  # Get qualname
            remaining_memo = next(iter(memos.keys()))[1]  # Get qualname
            assert remaining_function == "func_b"
            assert remaining_memo == "func_b"


def test_cache_across_reloads_gc_across_modules():
    """Test gc behavior when functions in different modules are removed."""
    from reactivity.hmr.utils import functions, memos

    # Clear any existing state
    memos.clear()
    functions.clear()

    with environment() as env:
        env["module_a.py"] = """
        from reactivity.hmr import cache_across_reloads

        @cache_across_reloads
        def func_from_a():
            print("from module a")
            return "a"
        """

        env["module_b.py"] = """
        from reactivity.hmr import cache_across_reloads

        @cache_across_reloads
        def func_from_b():
            print("from module b")
            return "b"
        """

        env["main.py"] = """
        from module_a import func_from_a
        from module_b import func_from_b

        func_from_a()
        func_from_b()
        """

        with env.hmr("main.py"):
            assert env.stdout_delta == "from module a\nfrom module b\n"

            # Both modules' functions should be present
            assert len(memos) == 2
            assert len(functions) == 2

            # Verify functions are from different modules
            module_paths = {key[0].name for key in memos}
            assert "module_a.py" in module_paths
            assert "module_b.py" in module_paths

            # Remove function from module_a by emptying it
            env["module_a.py"] = """
        # Module A now has no cache_across_reloads functions
        def regular_func():
            pass
        """

            # Trigger reload by touching main.py
            env["main.py"].touch()

            # After reload, only module_b's function should remain
            assert len(memos) == 1
            assert len(functions) == 1

            remaining_path = next(iter(memos.keys()))[0].name
            assert remaining_path == "module_b.py"
