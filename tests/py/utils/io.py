import sys
from collections import UserString
from contextlib import contextmanager, redirect_stdout
from typing import IO


class StringIOWrapper(UserString, IO[str]):
    def write(self, s):
        self.data += s
        return len(s)

    offset = 0

    @property
    def delta(self):
        value = self[self.offset :]
        self.offset = len(self)
        return value


@contextmanager
def capture_stdout():
    with redirect_stdout(io := StringIOWrapper("")):  # type: ignore
        yield io


def current_lineno():
    """Return the line number of the caller."""
    return sys._getframe(1).f_lineno  # noqa: SLF001
