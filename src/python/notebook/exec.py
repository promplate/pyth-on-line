from contextlib import redirect_stderr, redirect_stdout

from pyodide.code import eval_code_async
from pyodide.console import Console

from .stream import StreamManager
from .traceback import get_clean_traceback


async def exec_source(filename: str, source: str, context, manager: StreamManager):
    with redirect_stdout(manager.stdout), redirect_stderr(manager.stderr):  # type: ignore
        try:
            value = await eval_code_async(source, context, filename=filename, optimize=0, dont_inherit=True)
            if value is not None:
                manager.items.append({"type": "repr", "text": repr(value)})
                return value

        except Exception as e:
            manager.stderr.write(get_clean_traceback(e, filename))

        finally:
            manager.sync()  # at least sync once


async def console_exec_source(filename: str, source: str, context, manager: StreamManager):
    console = Console(context, filename=filename, optimize=0, dont_inherit=True)
    with redirect_stdout(manager.stdout), redirect_stderr(manager.stderr):  # type: ignore
        for line in source.splitlines():
            future = console.push(line)
            if future.syntax_check == "complete":
                try:
                    value = await future
                    if value is not None:
                        manager.items.append({"type": "repr", "text": repr(value)})
                        manager.sync()
                    yield value

                except Exception:
                    future.exception()  # to prevent an annoying warning
                    assert future.formatted_error, future
                    manager.stderr.write(future.formatted_error)

            elif future.syntax_check == "syntax-error":
                assert future.formatted_error, future
                manager.stderr.write(future.formatted_error)

        manager.sync()  # at least sync once
