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
