from collections import UserDict
from collections.abc import Callable
from functools import wraps
from inspect import getsource, getsourcefile
from pathlib import Path
from types import FunctionType

from .. import create_memo
from .core import NamespaceProxy, ReactiveModule
from .hooks import post_reload, pre_reload

memos: dict[str, Callable] = {}
functions: dict[str, Callable] = {}
functions_last: set[str] = set()


@pre_reload
def swap():
    functions_last.update(functions)
    functions.clear()


@post_reload
def clear_memos():
    for func in functions_last:
        if func not in functions and func in memos:
            del memos[func]


def cache_across_reloads[T](func: Callable[[], T]) -> Callable[[], T]:
    file = getsourcefile(func)
    assert file is not None
    module = ReactiveModule.instances.get(Path(file).resolve())

    if module is None:
        from functools import cache

        return cache(func)  # type: ignore

    source = getsource(func)

    proxy: NamespaceProxy = module._ReactiveModule__namespace_proxy  # type: ignore  # noqa: SLF001

    func = FunctionType(func.__code__, DictProxy(proxy), func.__name__, func.__defaults__, func.__closure__)

    functions[source] = func

    if source in memos and source in functions_last:
        return memos[source]

    @wraps(func)
    @create_memo
    def wrapper() -> T:
        return functions[source]()

    memos[source] = wrapper

    return wrapper


class DictProxy(UserDict, dict):  # type: ignore
    def __init__(self, data):
        self.data = data


def load(module: ReactiveModule):
    return module.load()
