from pathlib import Path

from hottest._vendored_reactivity.hmr.core import HMR_CONTEXT as HOTTEST_CONTEXT
from hottest.reactive import ReactiveCollector, collect_module
from reactivity.hmr.core import HMR_CONTEXT
from utils import environment


def test_reloader_runs_an_added_definition():
    with environment() as env:
        env["test_example.py"] = "def test_one(): pass"
        from hottest.__main__ import Reloader

        reloader = Reloader()
        with HOTTEST_CONTEXT.effect(reloader.run_entry_file) as effect:
            assert "test_example.test_one PASS" in env.stdout_delta
            env["test_example.py"].replace("def test_one(): pass", "def test_one(): pass\ndef test_two(): pass")
            reloader.on_changes({Path("test_example.py").resolve()})
            assert env.stdout_delta == "\033ctest_example.test_two PASS\n"
        effect.dispose()


def test_added_definitions_are_collected_without_replacing_existing_derived():
    with environment() as env:
        env["test_example.py"] = "def test_one(): pass"
        env["main.py"] = "import test_example"
        with env.hmr("main.py"):
            runs = []
            collector = ReactiveCollector(lambda func: runs.append(func.__name__))

            def collect():
                collector.update(collect_module("test_example"))

            with HMR_CONTEXT.effect(collect) as collection:
                assert [*collector.tests] == ["test_example::test_one"]
                original = collector.tests["test_example::test_one"]
                with HMR_CONTEXT.untrack():
                    for test in collector.tests.values():
                        test()
                assert runs == ["test_one"]

                env["test_example.py"].replace("def test_one(): pass", "def test_one(): pass\ndef test_two(): pass")
                assert [*collector.tests] == ["test_example::test_one", "test_example::test_two"]
                assert collector.tests["test_example::test_one"] is original
                assert original not in collection.dependencies

                with HMR_CONTEXT.untrack():
                    for test in collector.tests.values():
                        test()
                assert runs == ["test_one", "test_two"]
