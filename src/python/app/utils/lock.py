from asyncio import Lock
from functools import wraps
from typing import Any, Callable, Coroutine


def with_lock[**P, T](func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Coroutine[Any, Any, T]]:
    lock = Lock()

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs):
        async with lock:
            return await func(*args, **kwargs)

    return wrapper
