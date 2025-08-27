from ast import parse
from collections import ChainMap
from inspect import getsource
from textwrap import dedent

from pytest import raises
from reactivity import Reactive, create_effect
from reactivity.hmr.exec_hack import fix_class_name_resolution
from utils import capture_stdout


def exec_with_hack(source: str, globals=None, locals=None):
    tree = fix_class_name_resolution(parse(dedent(source)))
    code = compile(tree, "<string>", "exec")
    exec(code, globals, locals)


def test_exec_within_chainmap():
    r = Reactive({"a": 0})
    map = type("ChainMap", (ChainMap, dict), {})(r)

    source = """
        from functools import lru_cache
        Int = int

        class A:
            a + a

            @lambda _, b=a: _() + "abc"
            @staticmethod
            def f():
                return str(a)

            print(f)

            @lru_cache(a or 0)
            def f(self, _: Int) -> Int:
                print(a)

        A().f(a)
    """

    with capture_stdout() as stdout, create_effect(lambda: exec_with_hack(source, map)):
        assert stdout.delta == "0abc\n0\n"
        r["a"] = 1
        assert stdout.delta == "1abc\n1\n"


def test_exec_within_default_dict():
    class DefaultDict(dict):
        def __missing__(self, key):
            print(key)
            return key

    source = """
        class _:
            def _(a: b, c=d, e: f = g) -> h: ...
    """

    with capture_stdout() as stdout:
        exec_with_hack(source, DefaultDict())

    assert stdout == "d\ng\nb\nf\nh\n"  # defaults and annotations printed in order


def test_no_parent_frame_namespace_leak():
    def main():
        def f():
            def g():
                class _:  # noqa: N801
                    print(value)  # noqa: F821  # type: ignore

            return g()

        def h():
            value = "wrong"  # noqa: F841
            f()

        h()

    with raises(NameError):
        main()

    with raises(NameError):
        exec_with_hack(dedent(getsource(main)) + "\n\nmain()")


def test_name_lookup():
    a = b = c = None  # noqa: F841

    def main():
        a = 1

        def f():
            b = 2

            def g():
                c = 3

                class _:  # noqa: N801
                    print(a, b, c)

            return g()

        f()

    with capture_stdout() as stdout:
        main()
        assert stdout.delta == "1 2 3\n"
        exec_with_hack(dedent(getsource(main)) + "\n\nmain()")
        assert stdout.delta == "1 2 3\n"
