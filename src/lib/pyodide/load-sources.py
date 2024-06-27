from importlib import import_module, invalidate_caches
from pathlib import Path
from sys import path as sys_path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...python import main

    sources: dict[str, str] = {}


temp = TemporaryDirectory(prefix="runtime_")
root = Path(temp.name)
for path, source in sources.items():
    file = root / path
    if not file.parent.is_dir():
        file.parent.mkdir(parents=True)
    file.write_text(source, "utf-8")

sys_path.insert(0, root.parent.as_posix())
globals().update(import_module(root.name).__dict__)


@main().add_done_callback
def _(_):
    temp.cleanup()
    sys_path.pop(0)
    invalidate_caches()
