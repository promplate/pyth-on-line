from asyncio import ensure_future
from functools import wraps
from inspect import isawaitable

from pyodide.ffi import JsProxy, create_proxy, to_js
from pyodide.webloop import PyodideTask


def _to_js[T](value):
    if isawaitable(value):
        promise: PyodideTask[T] = ensure_future(value)  # type: ignore
        return promise.then(to_js)

    return to_js(value)


def _to_py(value):
    return value.to_py() if isinstance(value, JsProxy) else value


def js_api(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return _to_js(func(*map(_to_py, args), **{k: _to_py(v) for k, v in kwargs.items()}))

    setattr(wrapper, "_is_js_api", True)

    return wrapper


def patch_api_methods(obj):
    for k, v in obj.__dict__.items():
        if callable(v) and getattr(v, "_is_js_api", True):
            setattr(obj, k, create_proxy(v))


class JsAPI:
    def __init__(self):
        patch_api_methods(self)
