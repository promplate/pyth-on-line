from pathlib import Path
from sys import modules
from sys import path as sys_path

root = Path("/runtime_sources/python")

sys_path.insert(0, root.as_posix())


def setup_module(sources: dict[str, str], module_name: str):
    for path, source in sources.items():
        file = root / module_name / path
        print(file)
        if not file.parent.is_dir():
            file.parent.mkdir(parents=True)
        file.write_text(source, "utf-8")

        if __debug__ and (name := path.replace("/", ".")) in modules:
            del modules[name]  # reload module at dev time


setup_module
