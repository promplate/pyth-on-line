from ast import parse
from collections import ChainMap
from textwrap import dedent

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
