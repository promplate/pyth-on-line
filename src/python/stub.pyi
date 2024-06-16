# This is a stub file for global variables provided by the js side of pyodide.

from collections.abc import Callable
from typing import TypeVar

Function = TypeVar("Function", bound=Callable)

def with_toast(*, loading: str, success: str = ..., duration: int = ...) -> Callable[[Function], Function]: ...
