from collections.abc import Awaitable, Callable

from pyodide.ffi import run_sync


def syncify[**P, T](func: Callable[P, Awaitable[T]]) -> Callable[P, T]:
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        return run_sync(func(*args, **kwargs))

    return wrapper
