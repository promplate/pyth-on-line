from collections import UserString
from contextlib import contextmanager, redirect_stdout
from typing import IO


class StringIOWrapper(UserString, IO[str]):
    def write(self, s):
        self.data += s
        return len(s)


@contextmanager
def capture_stdout():
    with redirect_stdout(io := StringIOWrapper("")):
        yield io
