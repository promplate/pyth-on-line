from contextlib import redirect_stderr, redirect_stdout

from pyodide.code import eval_code_async

from .stream import StreamManager
from .traceback import get_clean_traceback


async def exec_source(filename: str, source: str, context, manager: StreamManager):
    with redirect_stdout(manager.stdout), redirect_stderr(manager.stderr):  # type: ignore
        try:
            value = await eval_code_async(source, context, filename=filename)
            if value is not None:
                manager.items.append({"type": "repr", "text": repr(value)})
                manager.sync()
                return value

        except Exception as e:
            print(get_clean_traceback(e, filename), file=manager.stderr, end="")
