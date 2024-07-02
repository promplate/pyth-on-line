from pathlib import Path
from sys import modules
from sys import path as sys_path

from js import console

root = Path("/runtime_sources/")

sys_path.insert(0, root.as_posix())


def setup_module(sources: dict[str, str], module_name: str):
    console.groupCollapsed(module_name)

    for path, source in sources.items():
        file = root / module_name / path
        if not file.parent.is_dir():
            file.parent.mkdir(parents=True)
        file.write_text(source, "utf-8")

        console.groupCollapsed(path)
        console.log(source)
        console.groupEnd()

    console.groupEnd()

    if __debug__:
        for mod in list(modules):
            if mod.startswith(module_name):
                del modules[mod]  # reload module at dev time


setup_module
