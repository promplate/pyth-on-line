import sys
from functools import partial
from pathlib import Path
from typing import override

from termcolor import colored

from . import find_fixtures, find_test_functions, find_test_root, run_test
from ._vendored_reactivity.hmr.core import HMR_CONTEXT, SyncReloader
from ._vendored_reactivity.hmr.hooks import pre_reload
from .reactive import ReactiveCollector, collect_module

rootdir = find_test_root(Path.cwd())

if str(rootdir) not in sys.path:
    sys.path.insert(0, str(rootdir))


def _collector():
    fixtures = find_fixtures(rootdir)

    def run(func):
        print(colored(f"{func.__module__}.", attrs=["dark"]) + str(func.__qualname__), end=" ", flush=True)
        try:
            run_test(func, fixtures)
        except Exception:
            print(colored("FAIL", "red"))
        else:
            print(colored("PASS", "green"))

    return ReactiveCollector(run)


class Reloader(SyncReloader):
    def __init__(self):
        super().__init__("")
        self.collector = _collector()
        self.modules = dict.fromkeys(func.args[0].__module__ if isinstance(func, partial) else func.__module__ for func in find_test_functions(rootdir))

    @override
    def run_entry_file(self):
        @pre_reload
        def clear_terminal():
            print("\033c", end="", flush=True)

        for test in self.collector.update(ref for module in self.modules for ref in collect_module(module)):
            with HMR_CONTEXT.untrack():
                test()
        for test in self.collector.tests.values():
            if test.dirty:
                with HMR_CONTEXT.untrack():
                    test()
            else:
                test.track()


def main():
    Reloader().keep_watching_until_interrupt()


if __name__ == "__main__":
    main()
