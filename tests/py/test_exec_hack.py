from ast import parse
from collections import ChainMap
from textwrap import dedent

from reactivity import Reactive, create_effect
from reactivity.hmr.exec_hack import fix_class_name_resolution
from utils import capture_stdout


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

    tree = fix_class_name_resolution(parse(dedent(source)))
    code = compile(tree, filename="<string>", mode="exec")
    with capture_stdout() as stdout, create_effect(lambda: exec(code, map)):
        assert stdout.delta == "0abc\n0\n"
        r["a"] = 1
        assert stdout.delta == "1abc\n1\n"
