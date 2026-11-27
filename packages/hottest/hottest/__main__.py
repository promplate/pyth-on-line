import sys
from inspect import signature
from pathlib import Path
from typing import override

from termcolor import colored

from . import find_fixtures, find_test_root, run_test
from ._vendored_reactivity.hmr.core import HMR_CONTEXT, SyncReloader
from ._vendored_reactivity.hmr.fs import notify
from ._vendored_reactivity.hmr.hooks import pre_reload
from .collect import find_test_modules
from .reactive import ReactiveCollector, callable_signature, collect_module

rootdir = find_test_root(Path.cwd())

if str(rootdir) not in sys.path:
    sys.path.insert(0, str(rootdir))


def _collector():
    fixtures = {}

    def refresh():
        nonlocal fixtures
        fixtures = find_fixtures(rootdir)

    def extra_signature(func):
        extra_signature.current_fixtures = {name: fixtures[name] for name in signature(func).parameters.keys() & fixtures.keys()}
        return tuple((name, callable_signature(fixtures[name])) for name in signature(func).parameters.keys() & fixtures.keys())

    def run(func):
        print(colored(f"{func.__module__}.", attrs=["dark"]) + str(func.__qualname__), end=" ", flush=True)
        try:
            run_test(func, fixtures)
        except Exception:
            print(colored("FAIL", "red"))
        else:
            print(colored("PASS", "green"))

    return ReactiveCollector(run, extra_signature), refresh


class Reloader(SyncReloader):
    def __init__(self):
        super().__init__("")
        self.collector, self.refresh_fixtures = _collector()
        self.modules = sorted(set(find_test_modules(rootdir)))

    @override
    def on_changes(self, files):
        super().on_changes(files)
        for file in files:
            if file.name == "conftest.py":
                notify(file)

    @override
    def run_entry_file(self):
        self.refresh_fixtures()

        @pre_reload
        def clear_terminal():
            print("\033c", end="", flush=True)

        for test in self.collector.update(ref for module in self.modules for ref in collect_module(module, self.collector.extra_signature)):
            with HMR_CONTEXT.untrack():
                test()
        for test in self.collector.tests.values():
            if test.dirty:
                with HMR_CONTEXT.untrack():
                    test()
            test.track()


def main():
    Reloader().keep_watching_until_interrupt()


if __name__ == "__main__":
    main()
