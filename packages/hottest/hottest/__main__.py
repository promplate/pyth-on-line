import sys
from inspect import getsourcefile
from pathlib import Path
from typing import override

from . import find_fixtures, find_test_functions, find_test_root, run_test
from ._vendored_reactivity.hmr.core import HMR_CONTEXT, ReactiveModule, SyncReloader

RED = "\033[31m"
GREEN = "\033[32m"
DIM = "\033[2m"
RESET = "\033[0m"


def _main():
    rootdir = find_test_root(Path.cwd())

    if str(rootdir) not in sys.path:
        sys.path.insert(0, str(rootdir))

    fixtures = find_fixtures(rootdir)

    for func in find_test_functions(rootdir):

        @HMR_CONTEXT.effect
        def _(func=func):
            file = getsourcefile(func)
            assert file is not None
            module = ReactiveModule.instances[Path(file).resolve()]
            assert isinstance(module, ReactiveModule)
            func = getattr(module, func.__name__)

            print(f"{DIM}{func.__module__}.{RESET}{func.__qualname__}", end=" ", flush=True)
            try:
                run_test(func, fixtures)
            except Exception:
                print(f"{RED}FAIL{RESET}")
            else:
                print(f"{GREEN}PASS{RESET}")


class Reloader(SyncReloader):
    def __init__(self):
        super().__init__("")
        _main()

    @override
    def run_entry_file(self):
        pass


def main():
    Reloader().keep_watching_until_interrupt()


if __name__ == "__main__":
    main()
