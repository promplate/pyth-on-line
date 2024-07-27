import sys
from os import chdir
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...lib.pyodide.start.loader import setup_module
else:
    from __main__ import setup_module


class WorkspaceAPI:
    def __init__(self, sources: dict[str, str]):
        self._original_working_dir = Path.cwd()
        self.directory = TemporaryDirectory(prefix="workspace-", ignore_cleanup_errors=True)
        path = self.directory.name
        setup_module(sources, base_path=Path(path))
        chdir(path)
        sys.path.append(path)

    def close(self):
        chdir(self._original_working_dir)
        self.directory.cleanup()
        sys.path.remove(self.directory.name)
