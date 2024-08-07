import sys
from os import chdir
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from js import console

if TYPE_CHECKING:
    from ...lib.pyodide.start.loader import setup_module
else:
    from __main__ import setup_module


class WorkspaceAPI:
    def __init__(self, sources: dict[str, str]):
        self._original_working_dir = Path.cwd()
        self.directory = TemporaryDirectory(prefix="workspace-", ignore_cleanup_errors=True)
        base = self.directory.name
        setup_module(sources, base_path=Path(base))
        chdir(base)
        sys.path.insert(0, base)
        self.files = list(sources)

    def close(self):
        chdir(self._original_working_dir)
        self.directory.cleanup()
        sys.path.remove(self.directory.name)

    def sync(self, sources: dict[str, str], reload=True):
        base = self.directory.name

        for path in self.files:
            if path not in sources:
                Path(base, path).unlink()
                if reload:
                    unload(path2module(path))

        if reload:
            for path, content in sources.items():
                if Path(base, path).read_text() != content:
                    unload(path2module(path))

        setup_module(sources, base_path=Path(base))

    def save(self, path: str, content: str, reload=True):
        file = Path(self.directory.name, path)
        if file.read_text() != content:
            if reload:
                unload(path2module(path))

            if __debug__:
                from difflib import ndiff

                console.group(f"Updating %c{path}", "color: light-dark(peru,wheat)")
                console.log("\n".join(filter(lambda s: len(s) >= 2 and s[0] in "+-?" and s[1] == " ", ndiff(Path(self.directory.name, path).read_text().splitlines(), content.splitlines()))))
                console.groupEnd()

            file.write_text(content)


def path2module(filename: str):
    return filename.removesuffix(".py").replace("/", ".").replace(".__init__", "")


def unload(name: str):
    if "." in name:
        name = name[: name.index(".")]

    console.group(f"Unloading %c{name}.*", "color: light-dark(peru,wheat)")

    for module in [*sys.modules]:
        if module.startswith(f"{name}.") or module == name:
            del sys.modules[module]
            console.log(f"Unloaded %c{module.removeprefix(name) or "."}", "color: light-dark(peru,wheat)")

    console.groupEnd()
