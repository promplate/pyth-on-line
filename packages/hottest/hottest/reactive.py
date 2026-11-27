from collections.abc import Callable
from dataclasses import dataclass
from functools import partial, update_wrapper, wraps
from importlib import import_module
from inspect import getattr_static, isclass, isfunction
from types import MethodType
from typing import Any

from ._vendored_reactivity import derived
from ._vendored_reactivity.hmr.core import HMR_CONTEXT, ReactiveModule
from ._vendored_reactivity.hmr.utils import load
from ._vendored_reactivity.primitives import Derived


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

    def update(self, refs):
        discovered = {ref.nodeid: ref for ref in refs}
        for nodeid in self.tests.keys() - discovered.keys():
            self.tests.pop(nodeid).dispose()
        for nodeid, ref in discovered.items():
            if nodeid not in self.tests:
                self.tests[nodeid] = self.make_test(ref)
                yield self.tests[nodeid]

    def make_test(self, ref: TestRef):
        @derived(check_equality=False, context=HMR_CONTEXT)
        def test():
            with HMR_CONTEXT.untrack():  # Replacing a test's function object must not rerun it; only its reactive dependencies should.
                func = ref.resolve()
            self.run(func)

        test.reactivity_loss_strategy = "ignore"  # Tests without reactive globals still have a valid dependency-free body.
        return test
