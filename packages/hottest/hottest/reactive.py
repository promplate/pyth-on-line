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


@dataclass(frozen=True)
class TestRef:
    module: str
    name: str
    method: str | None = None

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
        obj = getattr(import_module(self.module), self.name)
        if self.method:
            obj = getattr(obj, self.method)
        parts = []
        for func in _callable_chain(obj):
            if isinstance(func, partial):
                parts.append((func.args, func.keywords.copy()))
            elif isinstance(func, FunctionType):
                if version_info >= (3, 14):
                    from annotationlib import Format, get_annotations

                    annotations = get_annotations(func, format=Format.STRING)
                else:
                    annotations = repr(func.__annotations__)
                parts.append((_code_signature(func.__code__), func.__defaults__, func.__kwdefaults__, annotations))
        return parts

    def track_globals(self, func):
        for target in _callable_chain(func):
            if isinstance(target, FunctionType) and (module := ReactiveModule.instances.get(Path(target.__code__.co_filename).resolve())):
                track_global_names(module, _global_names(target.__code__))


def collect_module(module_name: str):
    module = import_module(module_name)
    if isinstance(module, ReactiveModule):
        load(module)
        names = ReactiveModule.__dir__(module)
    else:
        names = vars(module)
    for name in names:
        if name.startswith("test") and callable(getattr(module, name)):
            yield TestRef(module_name, name)
        elif name.startswith("Test") and isclass(obj := getattr(module, name)):
            for method_name in dir(obj):
                if method_name.startswith("test") and callable(getattr(obj, method_name)):
                    yield TestRef(module_name, name, method_name)


class ReactiveCollector:
    def __init__(self, run: Callable[[Callable[[], Any]], Any]):
        self.run = run
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
