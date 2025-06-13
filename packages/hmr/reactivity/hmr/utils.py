from collections import UserDict
from collections.abc import Callable
from functools import wraps
from inspect import getsource, getsourcefile
from pathlib import Path
from types import FunctionType

from ..helpers import Memoized
from .core import HMR_CONTEXT, NamespaceProxy, ReactiveModule
from .hooks import post_reload, pre_reload

memos: dict[str, Callable] = {}
functions: dict[str, Callable] = {}
functions_last: set[str] = set()


@pre_reload
def swap():
    """
    Prepares function state for a module reload by saving current functions and clearing the active function registry.
    
    Moves all current function entries to the previous cycle's set and resets the active functions dictionary.
    """
    functions_last.update(functions)
    functions.clear()


@post_reload
def clear_memos():
    """
    Removes memoized cache entries for functions that were present before reload but no longer exist.
    
    This function cleans up the global memoization store by deleting cached results for functions that have been removed after a module reload cycle.
    """
    for func in functions_last:
        if func not in functions and func in memos:
            del memos[func]


def cache_across_reloads[T](func: Callable[[], T]) -> Callable[[], T]:
    """
    Caches the result of a function across module reloads in a reactive environment.
    
    If the function belongs to a reactive module, preserves its memoized result and state across hot reloads by recreating the function with the current reactive namespace and returning a memoized wrapper. If the function is not part of a reactive module, falls back to standard Python function caching.
    """
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

    def wrapper() -> T:
        """
        Calls and returns the result of the cached function associated with the given source code.
        """
        return functions[source]()

    memos[source] = memo = Memoized(wrapper, context=HMR_CONTEXT)

    return wraps(func)(memo)


class DictProxy(UserDict, dict):  # type: ignore
    def __init__(self, data):
        """
        Initializes the proxy dictionary with the provided data.
        
        Args:
            data: The initial data to populate the proxy dictionary.
        """
        self.data = data


def load(module: ReactiveModule):
    """
    Invokes the load method on a ReactiveModule instance.
    
    Returns:
        The result of the module's load() method.
    """
    return module.load()
