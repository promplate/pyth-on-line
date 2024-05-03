# This is a stub file for global variables provided by the js side of pyodide.

from typing import Callable, TypeVar

Function = TypeVar("Function", bound=Callable)

def with_toast(*, loading: str, success: str = ..., duration: int = ...) -> Callable[[Function], Function]: ...
