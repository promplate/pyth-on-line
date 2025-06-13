from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

pre_reload_hooks: dict[str, Callable[[], Any]] = {}
post_reload_hooks: dict[str, Callable[[], Any]] = {}


def pre_reload[T](func: Callable[[], T]) -> Callable[[], T]:
    """
    Registers a function as a pre-reload hook.

    The decorated function will be called before a reload event occurs.
    """
    pre_reload_hooks[func.__name__] = func
    return func


def post_reload[T](func: Callable[[], T]) -> Callable[[], T]:
    """
    Registers a function as a post-reload hook.

    The decorated function will be called after a reload event occurs.
    """
    post_reload_hooks[func.__name__] = func
    return func


@contextmanager
def use_pre_reload(func):
    """
    Context manager that temporarily registers a function as a pre-reload hook.

    The function is added to the pre-reload hooks when entering the context and removed upon exiting, even if an exception occurs.

    Yields:
        The function being registered as a pre-reload hook.
    """
    pre_reload(func)
    try:
        yield func
    finally:
        pre_reload_hooks.pop(func.__name__, None)


@contextmanager
def use_post_reload(func):
    """
    Context manager that temporarily registers a function as a post-reload hook.

    The function is added to the post-reload hooks when entering the context and removed upon exiting, even if an exception occurs.

    Yields:
        The function being registered as a post-reload hook.
    """
    post_reload(func)
    try:
        yield func
    finally:
        post_reload_hooks.pop(func.__name__, None)


def call_pre_reload_hooks():
    """
    Invokes all registered pre-reload hook functions.

    Calls each function currently registered in the pre-reload hooks registry without arguments.
    """
    for func in pre_reload_hooks.values():
        func()


def call_post_reload_hooks():
    """
    Invokes all registered post-reload hook functions.

    Calls each function currently registered in the post-reload hooks registry with no arguments.
    """
    for func in post_reload_hooks.values():
        func()
