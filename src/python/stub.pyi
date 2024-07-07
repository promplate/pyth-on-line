# This is a stub file for global variables provided by the js side of pyodide.

from collections.abc import Callable
from typing import Literal, TypeVar

Function = TypeVar("Function", bound=Callable)

class Toast[Id]:
    def dismiss(self, id: Id): ...
    def loading(self, message: str, *, id: Id | None = None, promise: Literal[True]) -> Id: ...  # promise=True to support animation
    def message(self, message: str, *, id: Id | None = None, duration: int | None = None) -> Id: ...
    info = error = warning = success = message

toast: Toast[str]

__all__ = ["toast"]
