from collections.abc import Callable
from dataclasses import dataclass
from dis import get_instructions
from functools import partial, update_wrapper, wraps
from importlib import import_module
from inspect import getattr_static, isclass, isfunction
from pathlib import Path
from sys import version_info
from types import CodeType, FunctionType, MethodType
from typing import Any

from ._vendored_reactivity import derived
from ._vendored_reactivity.hmr.core import HMR_CONTEXT, ReactiveModule
from ._vendored_reactivity.hmr.utils import load, track_global_names
from ._vendored_reactivity.primitives import Derived


def _callable_chain(obj):
    seen = set()
    while obj is not None and id(obj) not in seen:
        seen.add(id(obj))
        yield obj
        if isinstance(obj, partial):
            obj = obj.func
        elif isinstance(obj, MethodType):
            obj = obj.__func__
        else:
            obj = getattr(obj, "__wrapped__", None)


def _code_signature(code: CodeType) -> CodeType:
    constants = tuple(_code_signature(value) if isinstance(value, CodeType) else value for value in code.co_consts)
    return code.replace(co_firstlineno=1, co_linetable=b"", co_consts=constants)


def _global_names(code: CodeType):
    for instruction in get_instructions(code):
        if instruction.opname == "LOAD_GLOBAL":
            yield instruction.argval
    for value in code.co_consts:
        if isinstance(value, CodeType):
            yield from _global_names(value)


def _is_callable(value):
    return isinstance(value, (FunctionType, MethodType, partial)) and value.__module__ != __name__


def callable_signature(obj, seen=None):
    seen = set() if seen is None else seen
    if id(obj) in seen:
        return ()
    seen.add(id(obj))
    parts = []
    for func in _callable_chain(obj):
        if isinstance(func, partial):
            parts.append((func.args, func.keywords.copy()))
        elif isinstance(func, FunctionType):
            if func.__module__ == __name__ and func.__qualname__ == "TestRef.resolve.<locals>.run_method":
                continue
            if version_info >= (3, 14):
                from annotationlib import Format, get_annotations

                annotations = get_annotations(func, format=Format.STRING)
            else:
                annotations = repr(func.__annotations__)
            closure = tuple(
                cell.cell_contents
                if isinstance(cell.cell_contents, (str, int, float, bool, bytes, type(None)))
                else callable_signature(cell.cell_contents, seen)
                if _is_callable(cell.cell_contents)
                else repr(cell.cell_contents)
                for cell in func.__closure__ or ()
            )
            parts.append((_code_signature(func.__code__), func.__defaults__, func.__kwdefaults__, annotations, closure))
            if module := ReactiveModule.instances.get(Path(func.__code__.co_filename).resolve()):
                names = set(_global_names(func.__code__)) - set(func.__code__.co_freevars)
                parts.append(tuple((name, callable_signature(value, seen)) for name in sorted(names) if _is_callable(value := vars(module).get(name))))
    return tuple(parts)


def _class_signature(cls):
    return tuple(
        (name, callable_signature(value) if _is_callable(value) else repr(value))
        for name, value in vars(cls).items()
        if not name.startswith("test") and not (name.startswith("__") and name.endswith("__"))
    )


def track_callable_globals(obj, seen=None):
    seen = set() if seen is None else seen
    if id(obj) in seen:
        return
    seen.add(id(obj))
    for target in _callable_chain(obj):
        if not isinstance(target, FunctionType) or not (module := ReactiveModule.instances.get(Path(target.__code__.co_filename).resolve())):
            continue
        names = tuple(set(_global_names(target.__code__)) - set(target.__code__.co_freevars))
        track_global_names(module, (name for name in names if not _is_callable(vars(module).get(name))))
        for name in names:
            if _is_callable(value := vars(module).get(name)):
                track_callable_globals(value, seen)


@dataclass(frozen=True)
class TestRef:
    module: str
    name: str
    method: str | None = None
    extra_signature: Callable = lambda _: ()

    @property
    def nodeid(self):
        return f"{self.module}::{self.name}" + (f"::{self.method}" if self.method else "")

    def resolve(self):
        obj = getattr(import_module(self.module), self.name)
        if name := self.method:
            method = getattr(obj, name)
            if isfunction(getattr_static(obj, name)):
                method = MethodType(method, obj)  # Expose the bound signature without constructing an instance until the test runs.

            @wraps(method)
            def run_method(*args, **kwargs):
                return getattr(obj(), name)(*args, **kwargs)

            return run_method
        if not hasattr(obj, "__qualname__"):
            func = update_wrapper(partial(obj), obj)
            func.__module__, func.__qualname__ = self.module, self.name
            return func
        return obj

    def signature(self):
        cls = getattr(import_module(self.module), self.name)
        obj = cls
        if self.method:
            obj = getattr(obj, self.method)
        return callable_signature(obj), self.extra_signature(obj), _class_signature(cls) if self.method else ()

    def track_globals(self, func):
        track_callable_globals(func)
        for fixture in getattr(self.extra_signature, "current_fixtures", {}).values():
            track_callable_globals(fixture)


def collect_module(module_name: str, extra_signature=lambda _: ()):
    module = import_module(module_name)
    if isinstance(module, ReactiveModule):
        load(module)
        names = ReactiveModule.__dir__(module)
    else:
        names = vars(module)
    for name in names:
        if name.startswith("test") and callable(getattr(module, name)):
            yield TestRef(module_name, name, extra_signature=extra_signature)
        elif name.startswith("Test") and isclass(obj := getattr(module, name)):
            for method_name in dir(obj):
                if method_name.startswith("test") and callable(getattr(obj, method_name)):
                    yield TestRef(module_name, name, method_name, extra_signature)


class ReactiveCollector:
    def __init__(self, run: Callable[[Callable[[], Any]], Any], extra_signature=lambda _: ()):
        self.run = run
        self.extra_signature = extra_signature
        self.tests: dict[str, Derived] = {}
        self.signatures = {}

    def update(self, refs):
        discovered = {ref.nodeid: ref for ref in refs}
        for nodeid in self.tests.keys() - discovered.keys():
            self.tests.pop(nodeid).dispose()
            self.signatures.pop(nodeid)
        for nodeid, ref in discovered.items():
            try:
                signature = ref.signature()
                changed = nodeid in self.tests and self.signatures[nodeid] != signature
            except Exception:
                # Reading annotations and comparing defaults can run user code. Rerun this test if comparison fails.
                signature = object()
                changed = nodeid in self.tests
            if changed:
                self.tests[nodeid].invalidate()
            self.signatures[nodeid] = signature
            if nodeid not in self.tests:
                self.tests[nodeid] = self.make_test(ref)
                yield self.tests[nodeid]

    def make_test(self, ref: TestRef):
        @derived(check_equality=False, context=HMR_CONTEXT)
        def test():
            with HMR_CONTEXT.untrack():  # Replacing a test's function object must not rerun it; only its reactive dependencies should.
                func = ref.resolve()
            ref.track_globals(func)
            self.run(func)

        test.reactivity_loss_strategy = "ignore"  # Tests without reactive globals still have a valid dependency-free body.
        return test
