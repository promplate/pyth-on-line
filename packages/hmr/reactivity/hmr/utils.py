from ast import parse
from collections import UserDict
from collections.abc import Callable
from functools import wraps
from inspect import getsource, getsourcefile
from pathlib import Path
from types import FunctionType

from ..helpers import Memoized
from .core import HMR_CONTEXT, NamespaceProxy, ReactiveModule
from .exec_hack import fix_class_name_resolution
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


_cache_decorator_phase = False


def cache_across_reloads[T](func: Callable[[], T]) -> Callable[[], T]:
    file = getsourcefile(func)
    assert file is not None
    module = ReactiveModule.instances.get(Path(file).resolve())

    if module is None:
        from functools import cache

        return cache(func)  # type: ignore

    source = getsource(func)

    proxy: NamespaceProxy = module._ReactiveModule__namespace_proxy  # type: ignore  # noqa: SLF001

    global _cache_decorator_phase
    _cache_decorator_phase = not _cache_decorator_phase
    if _cache_decorator_phase:  # this function will be called twice: once transforming ast and once re-executing the patched source
        try:
            exec(compile(fix_class_name_resolution(parse(source), func.__code__.co_firstlineno - 1), file, "exec"), DictProxy(proxy))
        except _Return as e:
            # If this function is used as a decorator, it will raise an `_Return` exception in the second phase.
            return e.value
        else:
            # Otherwise, it is used as a function, and we need to do the second phase ourselves.
            func = proxy[func.__name__]

    func = FunctionType(func.__code__, DictProxy(proxy), func.__name__, func.__defaults__, func.__closure__)

    functions[source] = func

    if source in memos and source in functions_last:
        return _return(memos[source])

    def wrapper() -> T:
        return functions[source]()

    memos[source] = memo = Memoized(wrapper, context=HMR_CONTEXT)

    return _return(wraps(func)(memo))


class _Return(Exception):  # noqa: N818
    def __init__(self, value):
        self.value = value
        super().__init__()


def _return[T](value: T) -> T:
    global _cache_decorator_phase

    if _cache_decorator_phase:
        _cache_decorator_phase = not _cache_decorator_phase
        return value

    raise _Return(value)  # used as decorator, so we raise an exception to jump before outer decorators


class DictProxy(UserDict, dict):  # type: ignore
    def __init__(self, data):
        self.data = data


def load(module: ReactiveModule):
    return module.load()
