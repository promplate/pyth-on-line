from ast import parse
from collections import ChainMap
from collections.abc import Mapping
from contextlib import suppress
from typing import Any

from pure_eval import CannotEval, Evaluator


def _format_inspect(value):
    res = {"class": type(value).__qualname__}

    match value:
        case type():
            res |= {
                "value": f"{value.__qualname__}({', '.join(cls.__qualname__ for cls in value.__bases__)})",
                "type": "exception" if issubclass(value, BaseException) else "class",
            }
        case _:
            res |= {"value": repr(value)}

    return res


def _literal_eval(source: str, namespace: Mapping[str, Any]):
    if value := getattr(parse(source).body[0], "value", None):  # body may have zero width
        return Evaluator(namespace)[value]

    raise SyntaxError


def inspect(name: str, *namespaces: dict[str, Any]):
    namespace = ChainMap(*namespaces)

    if name.isidentifier():
        with suppress(KeyError):
            return _format_inspect(namespace[name])
    else:
        with suppress(CannotEval, SyntaxError, IndexError):
            return _format_inspect(_literal_eval(name, namespace))
