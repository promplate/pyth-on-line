import sys
from pathlib import Path

from . import find_fixtures, find_test_functions, find_test_root, run_test

RED = "\033[31m"
GREEN = "\033[32m"
DIM = "\033[2m"
RESET = "\033[0m"


def main():
    rootdir = find_test_root(Path.cwd())

    if str(rootdir) not in sys.path:
        sys.path.insert(0, str(rootdir))

    fixtures = find_fixtures(rootdir)

    for func in find_test_functions(rootdir):
        print(f"{DIM}{func.__module__}.{RESET}{func.__qualname__}", end=" ", flush=True)
        try:
            run_test(func, fixtures)
        except Exception:
            print(f"{RED}FAIL{RESET}")
        else:
            print(f"{GREEN}PASS{RESET}")


if __name__ == "__main__":
    main()
