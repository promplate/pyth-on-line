from pathlib import Path
from sys import modules
from sys import path as sys_path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    sources: dict[str, str] = {}


root = Path("/runtime_sources/python")
for path, source in sources.items():
    file = root / path
    if not file.parent.is_dir():
        file.parent.mkdir(parents=True)
    file.write_text(source, "utf-8")

sys_path.insert(0, root.parent.as_posix())
for name in list(modules):
    if name.startswith("python"):
        del modules[name]
        print(f"unloaded {name}")


from python import main


@main().add_done_callback
def _(_):
    sys_path.pop(0)
