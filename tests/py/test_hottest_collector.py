import sys
from importlib import import_module
from pathlib import Path

from hottest._vendored_reactivity.hmr import fs, hooks
from hottest._vendored_reactivity.hmr.core import HMR_CONTEXT as HOTTEST_CONTEXT
from hottest._vendored_reactivity.hmr.core import ReactiveModule, SyncReloader
from hottest.reactive import ReactiveCollector, collect_module
from pytest import fixture
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
            env["test_example.py"].replace("    def test_one(self): pass", "    def test_one(self): pass\n    def test_two(self, monkeypatch): assert monkeypatch is not None")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.TestGroup.test_two PASS\n"


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
