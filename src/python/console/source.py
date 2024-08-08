import sys
from pathlib import Path
from tempfile import TemporaryDirectory


class SourceFile:
    def __init__(self, filename: str):
        self.dir = tempdir = TemporaryDirectory(prefix="console-")
        sys.path.insert(0, tempdir.name)
        self.file = Path(tempdir.name) / filename
        self.lines = []

    def cleanup(self):
        self.dir.cleanup()
        sys.path.remove(self.dir.name)

    def sync(self):
        self.file.write_text("\n".join(self.lines))

    def push(self, source: str):
        self.lines.extend(source.splitlines())
        self.sync()

    @property
    def offset(self):
        return len(self.lines)

    def shift_source(self, source: str):
        return "\n" * self.offset + source
