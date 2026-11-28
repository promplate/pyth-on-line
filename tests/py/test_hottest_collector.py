import sys
from asyncio import to_thread
from importlib import import_module
from pathlib import Path

from hottest._vendored_reactivity.hmr import fs, hooks
from hottest._vendored_reactivity.hmr.core import HMR_CONTEXT as HOTTEST_CONTEXT
from hottest._vendored_reactivity.hmr.core import ReactiveModule, SyncReloader
from hottest.reactive import ReactiveCollector, collect_module
from pytest import fixture, mark
from utils import environment


@fixture(autouse=True)
def isolate_hottest(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setattr(hooks, "pre_reload_hooks", {})
    monkeypatch.setattr(hooks, "post_reload_hooks", {})
    monkeypatch.setattr(fs, "fs_signals", fs.fs_signals.copy())
    monkeypatch.setattr(ReactiveModule, "instances", ReactiveModule.instances.copy())
    meta_path, filters = sys.meta_path[:], fs._filters[:]  # noqa: SLF001
    computations = HOTTEST_CONTEXT.current_computations[:]
    batches = HOTTEST_CONTEXT.batches[:]
    yield
    sys.meta_path[:], fs._filters[:] = meta_path, filters  # noqa: SLF001
    HOTTEST_CONTEXT.current_computations[:] = computations
    HOTTEST_CONTEXT.batches[:] = batches


def test_reloader_runs_an_added_definition():
    with environment() as env:
        original = "def test_one(): assert all(True for _ in range(2))"
        env["test_example.py"] = original
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert "test_example.test_one PASS" in env.stdout_delta
            env["test_example.py"] = "def test_two(): pass\n" + original
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_two PASS\n"


@mark.parametrize(
    ("source", "before", "after", "result"),
    [
        ("x = 1\nclass TestGroup:\n    def test_one(self): assert all(x == i for i in [1])", "x = 1", "x = 2", "TestGroup.test_one FAIL"),
        ("def test_one(): assert missing == 1", "missing == 1", "missing == 1\nmissing = 1", "test_one PASS"),
        ("from functools import partial\ndef check(n): assert n == 1\ntest_one = partial(check, n=1)", "n=1", "n=2", "test_one FAIL"),
        ("from functools import wraps\ndef decorate(f):\n    @wraps(f)\n    def run(): return f()\n    return run\n@decorate\ndef test_one(): pass", "pass", "assert False", "test_one FAIL"),
        (
            "from functools import wraps\ndef guard(flag):\n    def decorate(func):\n        @wraps(func)\n        def run():\n            assert flag\n            return func()\n        return run\n    return decorate\n@guard(True)\ndef test_guarded(): pass",
            "guard(True)",
            "guard(False)",
            "test_guarded FAIL",
        ),
        ("class TestValues:\n    expected = 1\n    def test_value(self): assert self.expected == 1", "expected = 1", "expected = 2", "TestValues.test_value FAIL"),
        ("class TestValues:\n    test_data = 1\n    def test_value(self): assert self.test_data == 1", "test_data = 1", "test_data = 2", "TestValues.test_value FAIL"),
        ("class TestValues:\n    @staticmethod\n    def test_value(value=1): assert value == 1", "    @staticmethod\n", "", "TestValues.test_value FAIL"),
        ("def test_one(): pass\ntest_one.__signature__ = 'invalid'", "'invalid'", "None", "test_one PASS"),
        (
            "def limit(n):\n    class Limit:\n        def read(self): return n\n    return Limit()\n"
            "class TestLimits:\n    limits = [limit(1), limit(1)]\n    def test_one(self): assert self.limits[1].read() == 1",
            "[limit(1), limit(1)]",
            "[limit(1), limit(2)]",
            "TestLimits.test_one FAIL",
        ),
        (
            "from collections import namedtuple\ndef make():\n    Point = namedtuple('Point', 'x', module='virtual_model')\n"
            "    point = Point(1)\n    def check(): assert point.x == 1\n    return check\ntest_one = make()",
            "Point(1)",
            "Point(2)",
            "make.<locals>.check FAIL",
        ),
        (
            "class TestGroup:\n    __module__ = 'virtual_model'\n    value = 1\n    def test_one(self): assert self.value == 1",
            "value = 1",
            "value = 2",
            "TestGroup.test_one FAIL",
        ),
        (
            "from typing import NamedTuple\nclass Value(NamedTuple):\n    n: int\n    def answer(self): return 1\ndef make(values):\n    def check(): assert values[0].answer() == 1\n    return check\ntest_one = make([Value(0)])",
            "return 1",
            "return 2",
            "make.<locals>.check FAIL",
        ),
        (
            "from pytest import fixture\n@fixture\ndef value(): return 1\ndef test_one(value=True): assert value",
            "return 1",
            "return 2\ndef test_added(): pass",
            "test_added PASS",
        ),
        (
            "class TestValues:\n    values = {'a': 1, 'b': 2}\n    def test_first(self): assert next(iter(self.values)) == 'a'",
            "'a': 1, 'b': 2",
            "'b': 2, 'a': 1",
            "TestValues.test_first FAIL",
        ),
        (
            "class Row(dict):\n    __slots__ = ()\n    __getattr__ = dict.__getitem__\nrows = [Row(value=1)]\ndef test_row(): assert rows[0].value == 1",
            "rows[0].value == 1",
            "rows[0].value == 2",
            "test_row FAIL",
        ),
        (
            "class Row(dict): pass\nrow = Row(value=1)\ndef test_row(): assert row['value'] == 1",
            "row['value'] == 1",
            "row['value'] == 1\ndef test_added(): pass",
            "test_added PASS",
        ),
        ("from pytest import fixture\n@fixture\ndef value(): return 1\ndef test_one(value): assert value == 1", "return 1", "return 2", "test_one FAIL"),
    ],
)
def test_reloader_detects_changed_test_inputs(source, before, after, result):
    with environment() as env:
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert "test_example." in env.stdout_delta
            env["test_example.py"].replace(before, after)
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == f"\033ctest_example.{result}\n"


def test_reloader_detects_changed_class_valued_globals():
    with environment() as env:
        env["test_example.py"] = "class Value:\n    expected = 1\ndef test_one(): assert Value.expected == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_one PASS\n"
            env["test_example.py"].replace("expected = 1", "expected = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_one FAIL\n"


def test_reloader_tracks_instance_valued_global_types():
    with environment() as env:
        env["test_example.py"] = (
            "from typing import NamedTuple\nclass Value(NamedTuple):\n    value: int = 0\n    def expected(self): return 1\nvalue = Value()\ndef test_one(): assert value.expected() == 1"
        )
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_one PASS\n"
            env["test_example.py"].replace("return 1", "return 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_one FAIL\n"


def test_reloader_tracks_test_instance_aliases():
    with environment() as env:
        env["test_example.py"] = "class TestGroup:\n    expected = 1\n    def test_one(self): other = self; assert other.expected == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("expected = 1", "expected = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


@mark.parametrize(
    ("declaration", "test"),
    [
        ("value = Value()", "def test_one(): assert value.expected() == 1"),
        ("values = [Value()]", "def test_one(): assert values[0].expected() == 1"),
        ("", "def test_one(value=Value()): assert value.expected() == 1"),
    ],
)
def test_reloader_tracks_reachable_instance_types(declaration, test):
    with environment() as env:
        env["test_example.py"] = f"from typing import NamedTuple\nclass Value(NamedTuple):\n    value: int = 0\n    def expected(self): return 1\n{declaration}\n{test}"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_one PASS\n"
            env["test_example.py"].replace("return 1", "return 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_one FAIL\n"


def test_reloader_tracks_dynamic_class_attribute_names():
    with environment() as env:
        env["test_example.py"] = "ATTR = 'expected'\nclass TestGroup:\n    expected = 1\n    def test_one(self): assert getattr(self, ATTR) == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("expected = 1", "expected = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


@mark.parametrize(
    "source",
    [
        "from pytest import fixture\nclass Value:\n    expected = 1\n@fixture\ndef value(): return Value.expected\ndef test_one(value): assert value == 1",
        "class Value:\n    expected = 1\nclass TestGroup:\n    def helper(self): return Value.expected\n    def test_one(self): assert self.helper() == 1",
        "class Value:\n    expected = 1\nclass TestGroup:\n    def __init__(self): self.value = Value.expected\n    def test_one(self): assert self.value == 1",
    ],
)
def test_reloader_detects_classes_referenced_by_reachable_helpers(source):
    with environment() as env:
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert " PASS\n" in env.stdout_delta
            env["test_example.py"].replace("expected = 1", "expected = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta.endswith(" FAIL\n")


@mark.parametrize("expression", ["Value().method()", "Value().property"])
def test_reloader_tracks_globals_used_by_referenced_class_methods(expression):
    with environment() as env:
        env["test_example.py"] = f"X = 1\nclass Value:\n    def method(self): return X\n    @property\n    def property(self): return X\ndef test_one(): assert {expression} == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_one PASS\n"
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_one FAIL\n"


@mark.parametrize(
    "source",
    [
        "from pytest import fixture\nX = 1\nclass Value:\n    def method(self): return X\n@fixture\ndef value(): return Value().method()\ndef test_one(value): assert value == 1",
        "X = 1\nclass Value:\n    def method(self): return X\nclass TestGroup:\n    def helper(self): return Value().method()\n    def test_one(self): assert self.helper() == 1",
        "X = 1\nclass Value:\n    def method(self): return X\nclass TestGroup:\n    def __init__(self): self.value = Value().method()\n    def test_one(self): assert self.value == 1",
        "X = 1\nclass Outer:\n    class Value:\n        def method(self): return X\ndef test_one(): assert Outer.Value().method() == 1",
        "X = 1\nclass Value:\n    def method(self): return X\nclass TestGroup:\n    helper = Value\n    def test_one(self): assert self.helper().method() == 1",
    ],
)
def test_reloader_tracks_class_method_globals_from_reachable_helpers(source):
    with environment() as env:
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert " PASS\n" in env.stdout_delta
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta.endswith(" FAIL\n")


@mark.parametrize(
    "method",
    [
        "def run(self): return self.helper().method()\n    def test_one(self): assert self.run() == 1",
        "def __init__(self): self.value = self.helper().method()\n    def test_one(self): assert self.value == 1",
    ],
)
def test_reloader_tracks_class_valued_attributes_from_class_helpers(method):
    with environment() as env:
        env["test_example.py"] = "X = 1\nclass Value:\n    def method(self): return X\nclass TestGroup:\n    helper = Value\n    " + method
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


@mark.parametrize(
    ("container", "access"), [("[Value]", "self.helpers[0]"), ("{'value': Value}", "self.helpers['value']"), ("{Value}", "next(iter(self.helpers))"), ("{Value: 'value'}", "next(iter(self.helpers))")]
)
def test_reloader_tracks_class_valued_attribute_containers(container, access):
    with environment() as env:
        env["test_example.py"] = f"X = 1\nclass Value:\n    def method(self): return X\nclass TestGroup:\n    helpers = {container}\n    def test_one(self): assert {access}().method() == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


@mark.parametrize(("helper", "expression"), [("Helper()", "self.helper.method()"), ("[Helper()]", "self.helper[0].method()"), ("Helper()", "self.helper()")])
def test_reloader_tracks_object_valued_class_attributes(helper, expression):
    with environment() as env:
        env["test_example.py"] = (
            f"X = 1\nclass Helper:\n    def method(self): return X\n    def __call__(self): return X\nclass TestGroup:\n    helper = {helper}\n    def test_one(self): assert {expression} == 1"
        )
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_detects_object_valued_class_helper_source_changes():
    with environment() as env:
        env["test_example.py"] = "class Helper:\n    def method(self): return 1\nclass TestGroup:\n    helper = Helper()\n    def test_one(self): assert self.helper.method() == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("return 1", "return 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


@mark.parametrize("attributes", ["", "    def __init__(self): self.value = 1", "    __slots__ = 'value'\n    def __init__(self): self.value = 1"])
def test_reloader_detects_object_helper_method_and_class_attribute_changes(attributes):
    with environment() as env:
        source = (
            f"class Helper:\n    factor = 1\n{attributes}\n    def method(self): return self.factor\nclass TestGroup:\n    helper = Helper()\n    def test_one(self): assert self.helper.method() == 1"
        )
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("return self.factor", "return 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"
            env["test_example.py"].replace("return 2", "return self.factor")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("factor = 1", "factor = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_tracks_class_valued_globals_in_class_attribute_containers():
    with environment() as env:
        env["test_example.py"] = "X = 1\nclass Other:\n    def method(self): return X\nclass Value:\n    helpers = [Other]\ndef test_one(): assert Value.helpers[0]().method() == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_one PASS\n"
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_one FAIL\n"


def test_reloader_tracks_globals_used_by_partial_class_helpers():
    with environment() as env:
        env["test_example.py"] = "from functools import partial\nX = 1\ndef f(): return X\nclass TestGroup:\n    helper = staticmethod(partial(f))\n    def test_one(self): assert self.helper() == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


@mark.parametrize("expression", ["super().expected", "super().helper()"])
def test_reloader_tracks_super_class_attributes(expression):
    with environment() as env:
        env["test_example.py"] = f"X = 1\nclass Base:\n    expected = X\n    def helper(self): return X\nclass TestGroup(Base):\n    def test_one(self): assert {expression} == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


@mark.parametrize("expression", ['getattr(self, "expected")', 'name = "expected"; assert getattr(self, name) == 1'])
def test_reloader_tracks_dynamically_accessed_class_attributes(expression):
    with environment() as env:
        assertion = expression if expression.startswith("name =") else f"assert {expression} == 1"
        env["test_example.py"] = f"X = 1\nclass TestGroup:\n    expected = X\n    def test_one(self): {assertion}"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_treats_a_single_string_slot_as_stable():
    with environment() as env:
        source = "class Options:\n    __slots__ = 'value'\n    def __init__(self): self.value = 1\nclass TestGroup:\n    expected = Options()\n    def test_one(self): assert self.expected.value == 1"
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"] = source + "\ndef test_added(): pass"
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_added PASS\n"
            env["test_example.py"].replace("self.value = 1", "self.value = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_tracks_current_class_through_a_module_alias():
    with environment() as env:
        env["test_example.py"] = "X = 1\nclass TestGroup:\n    expected = X\n    def test_one(self): assert Alias.expected == 1\nAlias = TestGroup"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_tracks_classes_captured_in_closures():
    with environment() as env:
        env["test_example.py"] = "class Value:\n    expected = 1\ndef make():\n    V = Value\n    def test_one(): assert V.expected == 1\n    return test_one\ntest_one = make()"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.make.<locals>.test_one PASS\n"
            env["test_example.py"].replace("expected = 1", "expected = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.make.<locals>.test_one FAIL\n"


def test_reloader_detects_changed_xfail_marker():
    with environment() as env:
        env["test_example.py"] = "from pytest import mark\n@mark.xfail\ndef test_one(): assert False"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_one PASS\n"
            env["test_example.py"].replace("@mark.xfail\n", "")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_one FAIL\n"


def test_reloader_does_not_evaluate_annotations_for_fixture_discovery():
    with environment() as env:
        env["test_example.py"] = "from __future__ import annotations\ndef test_bad() -> Missing: pass\ndef test_good(): pass"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_bad PASS\ntest_example.test_good PASS\n"


def test_default_comparison_cannot_interrupt_collection():
    with environment() as env:
        source = "class Options:\n    def __eq__(self, other): raise ValueError\ndef test_existing(value=Options()): pass"
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_existing PASS\n"
            env["test_example.py"] = source + "\ndef test_added(): pass"
            reloader.on_changes({Path("test_example.py").resolve()})
            assert "test_example.test_added PASS" in env.stdout_delta


def test_reloader_tracks_class_attributes_used_by_nested_code():
    with environment() as env:
        env["test_example.py"] = "def make(): return 1\nclass TestGroup:\n    expected = make()\n    def test_one(self): assert all(self.expected == 1 for _ in range(1))"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("return 1", "return 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_ignores_globals_used_only_by_sibling_tests_and_locals():
    with environment() as env:
        source = "X = 1\nY = 1\nclass TestGroup:\n    def test_one(self): Y = 1; assert X == Y\n    def test_two(self): assert Y == 1"
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\ntest_example.TestGroup.test_two PASS\n"
            env["test_example.py"] = source + "\ndef test_added(): pass"
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_added PASS\n"
            env["test_example.py"].replace("Y = 1\nclass", "Y = 2\nclass")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_two FAIL\n"


def test_reloader_treats_builtin_class_attributes_as_stable():
    with environment() as env:
        source = "class TestGroup:\n    error = ValueError\n    def test_one(self): pass"
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"] = source + "\ndef test_added(): pass"
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_added PASS\n"


def test_reloader_tracks_globals_used_by_base_class_expressions():
    with environment() as env:
        env["test_example.py"] = (
            "use_right = False\nclass Left:\n    expected = 1\nclass Right:\n    expected = 2\nclass TestGroup(Right if use_right else Left):\n    def test_one(self): assert self.expected == 1"
        )
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("use_right = False", "use_right = True")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


@mark.parametrize(
    ("method", "assertion"),
    [
        ("def __init__(self): self.value = X", "assert TestGroup().value == 1"),
        ("def __new__(cls): instance = super().__new__(cls); instance.value = X; return instance", "assert TestGroup().value == 1"),
        ("def __eq__(self, other): return self is not other and X == 1", "assert TestGroup() == TestGroup()"),
        ("def __len__(self): return X", "assert len(TestGroup()) == 1"),
        ("def __iter__(self): return iter([X])", "assert list(TestGroup()) == [1]"),
        ("def __getitem__(self, key): return X", "assert TestGroup()[0] == 1"),
        ("def __bool__(self): return X == 1", "assert TestGroup()"),
        ("def __call__(self): return X", "assert TestGroup()() == 1"),
        ("def __setattr__(self, name, value): object.__setattr__(self, name, X)", "instance = TestGroup(); instance.value = 0; assert instance.value == 1"),
        ("def __add__(self, other): return X", "assert TestGroup() + 1 == 1"),
        ("def __radd__(self, other): return X", "assert 1 + TestGroup() == 1"),
        ("def __iadd__(self, other): self.value = X; return self", "instance = TestGroup(); instance += 1; assert instance.value == 1"),
        ("def __enter__(self): return self\n    def __exit__(self, *args): self.value = X", "instance = TestGroup(); instance.__enter__(); instance.__exit__(); assert instance.value == 1"),
    ],
)
def test_reloader_tracks_globals_used_by_implicit_dunders(method, assertion):
    with environment() as env:
        env["test_example.py"] = "X = 1\nclass TestGroup:\n    " + method + "\n    def test_one(self): " + assertion
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_tracks_globals_used_by_context_manager_protocol():
    with environment() as env:
        env["test_example.py"] = (
            "X = 1\nclass TestGroup:\n    def __enter__(self): return self\n    def __exit__(self, *args): self.value = X\n    def test_one(self):\n        with TestGroup() as instance: pass\n        assert instance.value == 1"
        )
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_detects_changed_constructor_source():
    with environment() as env:
        env["test_example.py"] = "class TestGroup:\n    def __init__(self): self.value = 1\n    def test_one(self): assert TestGroup().value == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("self.value = 1", "self.value = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


@mark.parametrize(
    "method",
    [
        "@staticmethod\n    def test_one(): assert TestGroup.expected == 1",
        "def test_one(this): assert this.expected == 1",
        "def test_one(self): assert all(self.expected == 1 for _ in range(1))",
        "def test_one(self): assert self.__class__.expected == 1",
        "def test_one(self): assert type(self).expected == 1",
    ],
)
def test_reloader_tracks_attributes_for_class_and_instance_receivers(method):
    with environment() as env:
        env["test_example.py"] = "X = 1\nclass TestGroup:\n    expected = X\n    " + method
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_ignores_unrelated_class_attributes_and_handles_annotations():
    with environment() as env:
        source = "from types import SimpleNamespace\nX = 1\nY = 1\nclass TestGroup:\n    value = X\n    annotated: int\n    def __init__(self): self.instance = SimpleNamespace(value=Y)\n    def test_one(self): assert self.instance.value == 1\n    def test_two(self): assert self.value == 1"
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\ntest_example.TestGroup.test_two PASS\n"
            env["test_example.py"].replace("X = 1", "X = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_two FAIL\n"


def test_reloader_treats_nested_class_attributes_as_stable():
    with environment() as env:
        source = "class Namespace:\n    class Value:\n        number = 1\nclass TestGroup:\n    Helper = Namespace.Value\n    def test_one(self): assert self.Helper.number == 1"
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"] = source + "\ndef test_added(): pass"
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_added PASS\n"


def test_reloader_ignores_shadowed_base_class_attributes():
    with environment() as env:
        source = "X = 1\nY = 1\nclass Base:\n    expected = X\nclass TestGroup(Base):\n    expected = Y\n    def test_one(self): assert self.expected == 1"
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"] = source.replace("X = 1", "X = 2") + "\ndef test_added(): pass"
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_added PASS\n"


def test_reloader_detects_changed_class_attribute_values():
    with environment() as env:
        source = "class Options:\n    __slots__ = ('value',)\n    def __init__(self, value): self.value = value\n    def __eq__(self, other): raise ValueError\n    def __repr__(self): raise ValueError\nclass TestGroup:\n    expected = Options(1)\n    @property\n    def answer(self): return self.expected.value\n    def test_one(self): assert self.answer == 1"
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"] = source + "\ndef test_added(): pass"
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_added PASS\n"
            env["test_example.py"].replace("Options(1)", "Options(2)")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_snapshots_inherited_slots():
    with environment() as env:
        env["test_example.py"] = (
            "class Base:\n    __slots__ = ('value',)\n    def __init__(self, value): self.value = value\nclass Child(Base): pass\ndef make(): return Child(1)\nclass TestGroup:\n    expected = make()\n    def test_one(self): assert self.expected.value == 1"
        )
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("Child(1)", "Child(2)")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_treats_classes_inside_containers_as_stable():
    with environment() as env:
        source = "class Helper:\n    value = 1\nclass TestGroup:\n    helpers = [Helper]\n    def test_one(self): assert self.helpers[0].value == 1"
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"] = source + "\ndef test_added(): pass"
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_added PASS\n"


def test_reloader_treats_classes_used_as_dict_keys_as_stable():
    with environment() as env:
        source = "class Helper:\n    value = 1\nclass TestGroup:\n    helpers = {Helper: 'yes'}\n    def test_one(self): assert self.helpers[Helper] == 'yes'"
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"] = source + "\ndef test_added(): pass"
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_added PASS\n"


@mark.parametrize(
    "source",
    [
        "class A: pass\nclass B:\n    a = A\nA.b = B\nclass TestGroup:\n    helper = A\n    def test_one(self): assert self.helper.b.a is A",
        "class Helper: pass\nHelper.singleton = Helper()\nclass TestGroup:\n    def test_one(self): assert Helper.singleton is not None",
    ],
)
def test_reloader_handles_cyclic_class_attributes(source):
    with environment() as env:
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"] = source + "\ndef test_added(): pass"
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_added PASS\n"


def test_reloader_treats_namedtuple_attributes_as_stable():
    with environment() as env:
        source = "from collections import namedtuple\nPoint = namedtuple('Point', 'x y')\nclass TestGroup:\n    point = Point(1, 2)\n    def test_one(self): assert self.point.x == 1"
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"] = source + "\ndef test_added(): pass"
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_added PASS\n"


def test_reloader_tracks_globals_used_by_class_helpers():
    with environment() as env:
        env["test_example.py"] = "x = 1\nclass TestGroup:\n    def helper(self): return x\n    def test_one(self): assert self.helper() == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("x = 1", "x = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


@mark.parametrize(
    "method",
    [
        "@property\n    def helper(self): return x\n    def test_one(self): assert self.helper == 1",
        "@staticmethod\n    def helper(): return x\n    def test_one(self): assert self.helper() == 1",
        "@classmethod\n    def helper(cls): return x\n    def test_one(self): assert self.helper() == 1",
        "from functools import cached_property\n    @cached_property\n    def helper(self): return x\n    def test_one(self): assert self.helper == 1",
    ],
)
def test_reloader_tracks_globals_used_by_class_descriptors(method):
    with environment() as env:
        env["test_example.py"] = "x = 1\nclass TestGroup:\n    " + method
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("x = 1", "x = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_tracks_globals_used_by_inherited_helpers():
    with environment() as env:
        env["test_example.py"] = "x = 1\nclass Helpers:\n    def helper(self): return x\nclass TestGroup(Helpers):\n    def test_one(self): assert self.helper() == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("x = 1", "x = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_does_not_rerun_sibling_methods_for_method_only_edits():
    with environment() as env:
        env["test_example.py"] = "class TestGroup:\n    def test_one(self): pass\n    def test_two(self): pass"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\ntest_example.TestGroup.test_two PASS\n"
            env["test_example.py"].replace("def test_one(self): pass", "def test_one(self): assert False")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"


def test_reloader_tracks_class_attribute_dependencies_and_inherited_source():
    with environment() as env:
        env["test_example.py"] = "x = 1\ndef make(): return x\nclass Helpers:\n    expected = make()\nclass TestGroup(Helpers):\n    def test_one(self): assert self.expected == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("x = 1", "x = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"
            env["test_example.py"].replace("return x", "return 1")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one PASS\n"


def test_reloader_tracks_inherited_class_attributes_and_methods():
    with environment() as env:
        env["test_example.py"] = "class Helpers:\n    expected = 1\n    def helper(self): return self.expected\nclass TestGroup(Helpers):\n    def test_one(self): assert self.helper() == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("expected = 1", "expected = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"
            env["test_example.py"].replace("return self.expected", "return 1")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one PASS\n"


async def test_reloader_keeps_async_sibling_method_signatures_independent():
    def watch():
        with environment() as env:
            env["test_example.py"] = "class TestGroup:\n    async def test_one(self): pass\n    def test_two(self): pass"
            from hottest.__main__ import Reloader

            reloader = Reloader()
            with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
                assert env.stdout_delta == "test_example.TestGroup.test_one PASS\ntest_example.TestGroup.test_two PASS\n"
                env["test_example.py"].replace("async def test_one(self): pass", "async def test_one(self): assert False")
                reloader.on_changes({Path("test_example.py").resolve()})
                assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"

    await to_thread(watch)  # hottest calls asyncio.run() and owns the event loop in its thread.


def test_reloader_tracks_class_valued_attributes_and_inherited_slots():
    with environment() as env:
        source = "class Base:\n    __slots__ = ('value',)\n    def __init__(self, value): self.value = value\nclass Child(Base):\n    __slots__ = ()\nclass A:\n    value = 1\nclass B:\n    value = 2\nX = A\ndef make(): return Child(1)\nclass TestGroup:\n    Helper = X\n    expected = make()\n    allowed = {1, 2}\n    def test_one(self): assert self.Helper.value == 1\n    def test_two(self): assert self.expected.value == 1 and self.allowed == {1, 2}"
        env["test_example.py"] = source
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\ntest_example.TestGroup.test_two PASS\n"
            env["test_example.py"] = source + "\ndef test_added(): pass"
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_added PASS\n"
            env["test_example.py"].replace("Child(1)", "Child(2)")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_two FAIL\n"
            env["test_example.py"].replace("Child(2)", "Child(1)")
            env["test_example.py"].replace("X = A", "X = B")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert set(env.stdout_delta.removeprefix("\033c").splitlines()) == {"test_example.TestGroup.test_two PASS", "test_example.TestGroup.test_one FAIL"}


def test_reloader_reruns_only_a_modified_test():
    with environment() as env:
        env["test_example.py"] = "def test_one(): pass\ndef test_two(): pass"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_one PASS\ntest_example.test_two PASS\n"
            env["test_example.py"].replace("def test_two(): pass", "def test_two(): assert False\ndef test_three(): pass")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_three PASS\ntest_example.test_two FAIL\n"


def test_reloader_tracks_helpers_without_rerunning_on_unrelated_additions():
    with environment() as env:
        env["test_example.py"] = "def helper(): return 1\ndef test_one(): assert helper() == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_one PASS\n"
            env["test_example.py"].replace("assert helper() == 1", "assert helper() == 1\ndef test_two(): pass")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_two PASS\n"
            env["test_example.py"].replace("return 1", "return 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_one FAIL\n"


def test_reloader_reruns_when_a_module_global_changes():
    with environment() as env:
        env["test_example.py"] = "x = 1\ndef test_one(): assert x == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_one PASS\n"
            env["test_example.py"].replace("x = 1", "x = 2")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_one FAIL\n"


def test_reloader_tracks_helper_source_in_another_module():
    with environment() as env:
        env["helpers.py"] = "def value(): return 1"
        env["test_example.py"] = "from helpers import value\ndef test_one(): assert value() == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_one PASS\n"
            env["helpers.py"].replace("return 1", "return 2")
            reloader.on_changes({Path("helpers.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_one FAIL\n"


def test_reloader_discovers_fixtures_added_with_a_test():
    with environment() as env:
        env["test_example.py"] = ""
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            env["test_example.py"] = "from pytest import fixture\n@fixture\ndef value(): return 42\ndef test_added(value): assert value == 42"
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_added PASS\n"


def test_reloader_reloads_conftest_fixtures_repeatedly():
    with environment() as env:
        env["conftest.py"] = "from pytest import fixture\n@fixture\ndef value(): return 1"
        env["test_example.py"] = "def test_one(value): assert value == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_one PASS\n"
            for expected in (2, 3):
                env["conftest.py"].replace(f"return {expected - 1}", f"return {expected}")
                reloader.on_changes({Path("conftest.py").resolve()})
                assert env.stdout_delta == "\033ctest_example.test_one FAIL\n"


def test_reloader_tracks_globals_used_by_fixtures():
    with environment() as env:
        env["conftest.py"] = "from pytest import fixture\nx = 1\n@fixture\ndef value(): return x"
        env["test_example.py"] = "def test_one(value): assert value == 1"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_one PASS\n"
            env["conftest.py"].replace("x = 1", "x = 2")
            reloader.on_changes({Path("conftest.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_one FAIL\n"
            env["conftest.py"].replace("return x", "return 1")
            reloader.on_changes({Path("conftest.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_one PASS\n"


def test_reloader_collects_added_class_methods():
    with environment() as env:
        env["test_example.py"] = "class TestGroup:\n    def test_one(self): pass"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("    def test_one(self): pass", "    def test_one(self): assert False")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_one FAIL\n"
            env["test_example.py"].replace("    def test_one(self): assert False", "    def test_one(self): pass\n    def test_two(self, monkeypatch): assert monkeypatch is not None")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_two PASS\ntest_example.TestGroup.test_one PASS\n"


def test_reloader_collects_from_test_files():
    with environment() as env:
        env["helpers.py"] = "def test_imported(): pass\ndef test_unrelated(): assert False\ndef iter_namespace(): return 42"
        env["test_example.py"] = "from functools import partial\nfrom helpers import iter_namespace, test_imported\ndef check(): assert iter_namespace() == 42\ntest_partial = partial(check)"
        env["test_empty.py"].touch()
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "helpers.test_imported PASS\ntest_example.test_partial PASS\n"
            env["test_empty.py"] = "def test_first(): pass"
            reloader.on_changes({Path("test_empty.py").resolve()})
            assert env.stdout_delta == "\033ctest_empty.test_first PASS\n"


def test_reloader_tracks_a_test_invalidated_during_collection():
    with environment() as env:
        env["state.py"] = "from hottest._vendored_reactivity.hmr.core import HMR_CONTEXT\ns = HMR_CONTEXT.signal(0)"
        env["test_example.py"] = "from state import s\ndef test_read(): print(s.get())\ndef test_write(): s.set(1)"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_read 0\nPASS\ntest_example.test_write PASS\ntest_example.test_read 1\nPASS\n"
            import_module("state").s.set(2)
            assert env.stdout_delta == "test_example.test_read 2\nPASS\n"


def test_reloader_reruns_when_a_dependency_changes():
    with environment() as env:
        env["foo.py"] = "x = 1"
        env["test_example.py"] = "import foo\ndef test_one(): print(foo.x)"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.test_one 1\nPASS\n"
            env["foo.py"].replace("x = 1", "x = 2")
            reloader.on_changes({Path("foo.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_one 2\nPASS\n"


def test_added_definitions_are_collected_without_replacing_existing_derived():
    with environment() as env:
        env["test_example.py"] = "def test_one(): pass"
        reloader = SyncReloader("")
        import_module("test_example")

        runs = []
        collector = ReactiveCollector(lambda func: runs.append(func.__name__))

        def collect():
            return list(collector.update(collect_module("test_example")))

        with HOTTEST_CONTEXT.effect(collect) as collection:
            assert [*collector.tests] == ["test_example::test_one"]
            original = collector.tests["test_example::test_one"]
            with HOTTEST_CONTEXT.untrack():
                for test in collector.tests.values():
                    test()
            assert runs == ["test_one"]

            env["test_example.py"].replace("def test_one(): pass", "def test_one(): pass\ndef test_two(): pass")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert [*collector.tests] == ["test_example::test_one", "test_example::test_two"]
            assert collector.tests["test_example::test_one"] is original
            assert original not in collection.dependencies

            with HOTTEST_CONTEXT.untrack():
                for test in collector.tests.values():
                    test()
            assert runs == ["test_one", "test_two"]
