from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from typing import Any

from ._vendored_reactivity import derived
from ._vendored_reactivity.hmr.core import HMR_CONTEXT


@dataclass(frozen=True)
class TestRef:
    module: str
    name: str

    @property
    def nodeid(self):
        return f"{self.module}::{self.name}"

    def resolve(self):
        return getattr(import_module(self.module), self.name)


def collect_module(module_name: str):
    module = import_module(module_name)
    for name in module.iter_namespace():
        if name.startswith("test") and callable(getattr(module, name)):
            yield TestRef(module_name, name)


class ReactiveCollector:
    def __init__(self, run: Callable[[Callable[[], Any]], Any]):
        self.run = run
        self.tests: dict[str, Callable[[], Any]] = {}

    def update(self, refs):
        discovered = {ref.nodeid: ref for ref in refs}
        for nodeid in self.tests.keys() - discovered.keys():
            self.tests.pop(nodeid).dispose()
        for nodeid, ref in discovered.items():
            if nodeid not in self.tests:
                self.tests[nodeid] = self.make_test(ref)

    def make_test(self, ref: TestRef):
        @derived(check_equality=False, context=HMR_CONTEXT)
        def test():
            self.run(ref.resolve())

        test.reactivity_loss_strategy = "ignore"  # Tests without reactive globals still have a valid dependency-free body.
        return test
