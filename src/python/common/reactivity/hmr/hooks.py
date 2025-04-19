from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

pre_reload_hooks: dict[str, Callable[[], Any]] = {}
post_reload_hooks: dict[str, Callable[[], Any]] = {}


def pre_reload[T](func: Callable[[], T]) -> Callable[[], T]:
    pre_reload_hooks[func.__name__] = func
    return func


def post_reload[T](func: Callable[[], T]) -> Callable[[], T]:
    post_reload_hooks[func.__name__] = func
    return func


@contextmanager
def use_pre_reload(func):
    pre_reload(func)
    try:
        yield func
    finally:
        pre_reload_hooks.pop(func.__name__, None)


@contextmanager
def use_post_reload(func):
    post_reload(func)
    try:
        yield func
    finally:
        post_reload_hooks.pop(func.__name__, None)


def call_pre_reload_hooks():
    for func in pre_reload_hooks.values():
        func()


def call_post_reload_hooks():
    for func in post_reload_hooks.values():
        func()
