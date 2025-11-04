import sys


def current_lineno() -> int:
    return sys._getframe(1).f_lineno  # noqa: SLF001
