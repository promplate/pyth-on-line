from asyncio import iscoroutine, run
from collections.abc import Callable
from contextlib import ExitStack
from inspect import signature
from typing import Any

from pytest import Mark


def run_test(func: Callable[..., Any], fixtures: dict[str, Callable[[], Any]]):
    sig = signature(func)
    kwargs = {}

    try:
        with ExitStack() as stack:
            for param in sig.parameters.values():
                if param.name in fixtures and param.default is param.empty:
                    fixture = kwargs[param.name] = fixtures[param.name]()
                    if hasattr(fixture, "__enter__") and hasattr(fixture, "__exit__"):
                        kwargs[param.name] = stack.enter_context(fixture)
            ret = func(**kwargs)
            return run(ret) if iscoroutine(ret) else ret

    except Exception as e:
        marks: list[Mark] = getattr(func, "pytestmark", [])
        for mark in marks:
            if mark.name == "xfail":
                expected_exception = mark.kwargs.get("raises", Exception)
                if isinstance(e, expected_exception):
                    break
        else:
            raise
