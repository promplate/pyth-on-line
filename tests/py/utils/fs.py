from functools import partial
from pathlib import Path
from typing import final


class FsUtils:
    def write(self, filepath: str, content: str):
        Path(filepath).write_text(content)

    def replace(self, filepath: str, old: str, new: str):
        path = Path(filepath)
        path.write_text(path.read_text().replace(old, new))

    @final
    def __getitem__(self, filepath: str):
        class Replacer:
            replace = staticmethod(partial(self.replace, filepath))

        return Replacer()

    @final
    def __setitem__(self, filepath: str, content: str):
        self.write(filepath, content)
