# This is a stub file for global variables provided by the js side of pyodide.

from typing import Literal

class Toast[Id]:
    def dismiss(self, id: Id): ...
    def loading(self, message: str, *, id: Id | None = None, promise: Literal[True]) -> Id: ...  # promise=True to support animation
    def message(self, message: str, *, id: Id | None = None, duration: int | None = None) -> Id: ...
    info = message
    error = message
    warning = message
    success = message

toast: Toast[str]

__all__ = ["toast"]
