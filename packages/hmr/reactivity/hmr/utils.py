from ast import parse
from collections import UserDict
from collections.abc import Callable
from functools import wraps
from inspect import getsource, getsourcefile
from pathlib import Path
from types import FunctionType

from ..helpers import Derived
from .core import HMR_CONTEXT, NamespaceProxy, ReactiveModule
from .exec_hack import ABOVE_3_14, dedent, fix_class_name_resolution, is_future_annotations_enabled
from .hooks import on_dispose, post_reload

memos: dict[tuple[Path, str], tuple[Callable, str]] = {}  # (path, __qualname__) -> (memo, source)
functions: dict[tuple[Path, str], Callable] = {}  # (path, __qualname__) -> function


@post_reload
def gc_memos():
    for key in {*memos} - {*functions}:
        del memos[key]


_cache_decorator_phase = False


def cache_across_reloads[T](func: Callable[[], T]) -> Callable[[], T]:
    file = getsourcefile(func)
    assert file is not None
    module = ReactiveModule.instances.get(path := Path(file).resolve())

    if module is None:
        from functools import cache

        return cache(func)

    source, col_offset = dedent(getsource(func))

    key = (path, func.__qualname__)

    proxy: NamespaceProxy = module._ReactiveModule__namespace_proxy  # type: ignore  # noqa: SLF001
    flags: int = module._ReactiveModule__flags  # type: ignore  # noqa: SLF001
    skip_annotations = ABOVE_3_14 or is_future_annotations_enabled(flags)

    global _cache_decorator_phase
    _cache_decorator_phase = not _cache_decorator_phase
    if _cache_decorator_phase:  # this function will be called twice: once transforming ast and once re-executing the patched source
        on_dispose(lambda: functions.pop(key), file)
        try:
            exec(compile(fix_class_name_resolution(parse(source), func.__code__.co_firstlineno - 1, col_offset, skip_annotations), file, "exec", flags, dont_inherit=True), DictProxy(proxy))
        except _Return as e:
            # If this function is used as a decorator, it will raise an `_Return` exception in the second phase.
            return e.value
        else:
            # Otherwise, it is used as a function, and we need to do the second phase ourselves.
            func = proxy[func.__name__]

    func = FunctionType(func.__code__, DictProxy(proxy), func.__name__, func.__defaults__, func.__closure__)

    functions[key] = func

    if result := memos.get(key):
        memo, last_source = result
        if source != last_source:
            Derived.invalidate(memo)  # type: ignore
            memos[key] = memo, source
        return _return(wraps(func)(memo))

    @wraps(func)
    def wrapper() -> T:
        return functions[key]()

    memo = Derived(wrapper, context=HMR_CONTEXT)
    memos[key] = memo, source

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
