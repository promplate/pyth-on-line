"""
Usage:

fs: FsUtils

fs["filename"] = "content"
fs["filename"].replace("old", "new")
fs["filename"].touch()
"""

from functools import partial
from pathlib import Path
from textwrap import dedent
from typing import final


class FsUtils:
    def write(self, filepath: str, content: str):
        Path(filepath).write_text(content)

    def replace(self, filepath: str, old: str, new: str):
        path = Path(filepath)
        path.write_text(path.read_text().replace(old, new))

    def touch(self, filepath: str):
        path = Path(filepath)
        self.write(filepath, path.read_text() if path.exists() else "")

    @final
    def __getitem__(self, filepath: str):
        class Replacer:
            replace = staticmethod(partial(self.replace, filepath))
            touch = staticmethod(partial(self.touch, filepath))

        return Replacer()

    @final
    def __setitem__(self, filepath: str, content: str):
        self.write(filepath, dedent(content))
