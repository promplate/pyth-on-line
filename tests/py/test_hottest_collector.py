import sys
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
    monkeypatch.setattr(fs, "fs_signals", fs.fs_signals.copy())
    monkeypatch.setattr(ReactiveModule, "instances", ReactiveModule.instances.copy())
    meta_path, filters = sys.meta_path[:], fs._filters[:]  # noqa: SLF001
    yield
    sys.meta_path[:], fs._filters[:] = meta_path, filters  # noqa: SLF001


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
