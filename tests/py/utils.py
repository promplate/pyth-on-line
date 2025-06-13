from collections import UserString
from contextlib import contextmanager, redirect_stdout
from typing import IO


class StringIOWrapper(UserString, IO[str]):
    def write(self, s):
        """
        Appends the given string to the internal buffer.
        
        Args:
        	s: The string to append.
        
        Returns:
        	The number of characters written.
        """
        self.data += s
        return len(s)

    offset = 0

    @property
    def delta(self):
        """
        Returns the substring of the data from the current offset to the end, updating the offset to the current length.
        """
        value = self[self.offset :]
        self.offset = len(self)
        return value


@contextmanager
def capture_stdout():
    """
    Context manager that captures all output sent to standard output.
    
    Yields:
        StringIOWrapper: An object containing the captured output as a string.
    """
    with redirect_stdout(io := StringIOWrapper("")):  # type: ignore
        yield io
