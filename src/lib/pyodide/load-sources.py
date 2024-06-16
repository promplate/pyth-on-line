from importlib import import_module
from pathlib import Path
from sys import path as sys_path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from pyodide.http import pyfetch

if TYPE_CHECKING:
    from ...python import main


sources: dict[str, str] = await (await pyfetch("/sources")).json()  # type: ignore


with TemporaryDirectory() as temp:
    root = Path(temp)
    for path, source in sources.items():
        file = root / path
        if not file.parent.is_dir():
            file.parent.mkdir(parents=True)
        file.write_text(source, "utf-8")

    sys_path.insert(0, root.parent.as_posix())
    globals().update(import_module(root.name).__dict__)
    sys_path.pop(0)

    main()
