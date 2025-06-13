import sys
from contextlib import redirect_stderr, redirect_stdout

from pyodide.code import eval_code_async
from pyodide.console import Console
from reactivity.hmr.proxy import Proxy

from .stream import StreamManager
from .traceback import get_clean_traceback


class ReactiveNamespace(Proxy, dict):
    raw: dict


class PatchedConsole(Console):
    async def runcode(self, source, code):  # noqa: ARG002
        """
        Asynchronously executes compiled code within a reactive namespace environment.
        
        Runs the provided compiled code object using the raw dictionary of the reactive namespace as globals and the proxy as locals, ensuring standard output and error streams are flushed after execution.
        """
        assert isinstance(self.globals, ReactiveNamespace)
        with self.redirect_streams():
            try:
                return await code.run_async(self.globals.raw, self.globals)  # type: ignore
            finally:
                sys.stdout.flush()
                sys.stderr.flush()


async def exec_source(filename: str, source: str, context: ReactiveNamespace, manager: StreamManager):
    """
    Asynchronously executes a source code string within a reactive namespace, capturing output and errors.
    
    The function redirects standard output and error streams to the provided stream manager, evaluates the source code asynchronously using the raw and proxied contexts, and appends the result's representation to the manager if not None. Exceptions are caught and a cleaned traceback is written to the manager's stderr. The stream manager is synchronized after execution.
    
    Args:
        filename: The name of the file or cell being executed.
        source: The source code to execute.
        context: The reactive namespace providing globals and locals for execution.
        manager: The stream manager for capturing output and errors.
    
    Returns:
        The result of the evaluated source code if not None.
    """
    with redirect_stdout(manager.stdout), redirect_stderr(manager.stderr):  # type: ignore
        try:
            value = await eval_code_async(source, context.raw, context, filename=filename, optimize=0, dont_inherit=True)
            if value is not None:
                manager.items.append({"type": "repr", "text": repr(value)})
                return value

        except Exception as e:
            manager.stderr.write(get_clean_traceback(e, filename))

        finally:
            manager.sync()  # at least sync once


async def console_exec_source(filename: str, source: str, context, manager: StreamManager):
    """
    Asynchronously executes Python source code line-by-line in a reactive console environment.
    
    Each line is processed using a patched console that supports a reactive namespace. Output and errors are redirected to the provided stream manager. If a line completes successfully and returns a non-None value, its representation is appended to the manager's items and yielded. Syntax errors and exceptions are formatted and written to the manager's stderr. The stream manager is synchronized at least once after execution.
    """
    console = PatchedConsole(context, filename=filename, optimize=0, dont_inherit=True)
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
