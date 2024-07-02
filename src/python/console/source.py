import sys
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryDirectory


class SourceFile:
    def __init__(self, filename: str):
        for path in sys.path[:]:
            if (file := Path(path) / filename).is_file():
                file.unlink()
                sys.path.remove(path)

        with TemporaryDirectory(delete=False, prefix="console-") as tempdir:
            sys.path.append(tempdir)
            self.file = Path(tempdir) / filename

        self.lines = []

    def __del__(self):
        with suppress(Exception):
            self.file.unlink()
            sys.path.remove(str(self.file.parent))

    def sync(self):
        self.file.write_text("\n".join(self.lines))

    def push(self, line: str):
        self.lines.append(line)
        self.sync()

    def pop(self):
        self.lines.pop()
        self.sync()
