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
            self.file.unlink(missing_ok=True)
            sys.path.remove(str(self.file.parent))

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
