import sys
from collections.abc import Callable
from inspect import getsourcefile
from pathlib import Path
from typing import Any, override

from termcolor import colored

from . import find_fixtures, find_test_functions, find_test_root, run_test
from ._vendored_reactivity import derived
from ._vendored_reactivity.hmr.core import HMR_CONTEXT, ReactiveModule, SyncReloader
from ._vendored_reactivity.hmr.hooks import pre_reload

rootdir = find_test_root(Path.cwd())

if str(rootdir) not in sys.path:
    sys.path.insert(0, str(rootdir))


def _collect_tests():
    fixtures = find_fixtures(rootdir)

    tests: list[Callable[[], Any]] = []

    for func in find_test_functions(rootdir):

        @tests.append
        @derived(check_equality=False, context=HMR_CONTEXT)
        def _(func=func):
            file = getsourcefile(func)
            assert file is not None
            module = ReactiveModule.instances[Path(file).resolve()]
            assert isinstance(module, ReactiveModule)
            func = getattr(module, func.__name__)

            print(colored(f"{func.__module__}.", attrs=["dark"]) + str(func.__qualname__), end=" ", flush=True)
            try:
                run_test(func, fixtures)
            except Exception:
                print(colored("FAIL", "red"))
            else:
                print(colored("PASS", "green"))

    return tests


class Reloader(SyncReloader):
    def __init__(self):
        super().__init__("")
        self.tests = _collect_tests()

    @override
    def run_entry_file(self):
        @pre_reload
        def clear_terminal():
            print("\033c", end="", flush=True)

        for test in self.tests:
            test()


def main():
    Reloader().keep_watching_until_interrupt()


if __name__ == "__main__":
    main()
