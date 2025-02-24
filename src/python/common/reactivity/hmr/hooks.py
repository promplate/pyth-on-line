from collections.abc import Callable
from typing import Any

pre_reload_hooks: dict[str, Callable[[], Any]] = {}
post_reload_hooks: dict[str, Callable[[], Any]] = {}


def pre_reload[T](func: Callable[[], T]) -> Callable[[], T]:
    pre_reload_hooks[func.__name__] = func
    return func


def post_reload[T](func: Callable[[], T]) -> Callable[[], T]:
    post_reload_hooks[func.__name__] = func
    return func


def call_pre_reload_hooks():
    for func in pre_reload_hooks.values():
        func()


def call_post_reload_hooks():
    for func in post_reload_hooks.values():
        func()
