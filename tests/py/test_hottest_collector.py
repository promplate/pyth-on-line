import sys
from importlib import import_module
from pathlib import Path

from hottest._vendored_reactivity.hmr import fs
from hottest._vendored_reactivity.hmr.core import HMR_CONTEXT as HOTTEST_CONTEXT
from hottest._vendored_reactivity.hmr.core import SyncReloader
from hottest.reactive import ReactiveCollector, collect_module
from pytest import fixture
from utils import environment


@fixture(autouse=True)
def isolate_hottest(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    meta_path, filters = sys.meta_path[:], fs._filters[:]  # noqa: SLF001
    yield
    sys.meta_path[:], fs._filters[:] = meta_path, filters  # noqa: SLF001


def test_reloader_runs_an_added_definition():
    with environment() as env:
        env["test_example.py"] = "def test_one(): pass"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert "test_example.test_one PASS" in env.stdout_delta
            env["test_example.py"].replace("def test_one(): pass", "def test_one(): pass\ndef test_two(): pass")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_two PASS\n"


def test_reloader_collects_added_class_methods():
    with environment() as env:
        env["test_example.py"] = "class TestGroup:\n    def test_one(self): pass"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file):
            assert env.stdout_delta == "test_example.TestGroup.test_one PASS\n"
            env["test_example.py"].replace("    def test_one(self): pass", "    def test_one(self): pass\n    def test_two(self): pass")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_two PASS\n"


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
            [*collector.update(collect_module("test_example"))]

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
