from ast import AsyncFunctionDef, ClassDef, FunctionDef, dump, parse, walk
from collections.abc import Callable
from dataclasses import dataclass
from dis import get_instructions
from functools import cached_property, partial, update_wrapper, wraps
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
            with HMR_CONTEXT.untrack():
                obj = getattr(obj, "__wrapped__", None)


def _code_signature(code: CodeType) -> CodeType:
    constants = tuple(_code_signature(value) if isinstance(value, CodeType) else value for value in code.co_consts)
    return code.replace(co_firstlineno=1, co_linetable=b"", co_consts=constants)


def _global_names(code: CodeType):
    for instruction in get_instructions(code):
        if instruction.opname in {"LOAD_GLOBAL", "LOAD_NAME"}:
            yield instruction.argval
    for value in code.co_consts:
        if isinstance(value, CodeType):
            yield from _global_names(value)


def _attribute_names(code: CodeType):
    for instruction in get_instructions(code):
        if instruction.opname in {"LOAD_ATTR", "LOAD_METHOD"}:
            yield instruction.argval
    for value in code.co_consts:
        if isinstance(value, CodeType):
            yield from _attribute_names(value)


def _class_module(cls):
    if not isinstance(cls.__module__, str):
        return None
    with HMR_CONTEXT.untrack():
        module = import_module(cls.__module__)
        file = vars(module).get("__file__")
    return ReactiveModule.instances.get(Path(file).resolve()) if file else None


def _class_ast(module: ReactiveModule, name: str):
    with HMR_CONTEXT.untrack():
        source = Path(module.__dict__["__file__"]).read_text()
    body = parse(source).body
    for part in name.split("."):
        if part == "<locals>":
            return next((node for node in walk(body) if isinstance(node, ClassDef) and node.name == name.rsplit(".", 1)[-1]), None)
        if (node := next((node for node in body if isinstance(node, ClassDef) and node.name == part), None)) is None:
            return None
        body = node.body
    return node


def _is_callable(value):
    return isinstance(value, (FunctionType, MethodType, partial)) and value.__module__ != __name__


def _unwrap_descriptor(value):
    return value.func if isinstance(value, cached_property) else value.__func__ if isinstance(value, (staticmethod, classmethod)) else value.fget if isinstance(value, property) else value


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
                break
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


def _class_signature(module: ReactiveModule, name: str):
    node = _class_ast(module, name)
    if node is None:
        return None
    node.body = [child for child in node.body if not (isinstance(child, (FunctionDef, AsyncFunctionDef)) and child.name.startswith("test"))]
    return dump(node, include_attributes=False)


def _class_dependencies(cls, attributes=None):
    seen = set()
    for base in cls.__mro__:
        for name, value in vars(base).items():
            if name in seen or name.startswith("test") or (attributes is not None and name not in attributes):
                continue
            seen.add(name)
            callable_value = _unwrap_descriptor(value)
            if _is_callable(callable_value):
                yield name, callable_signature(callable_value)
            elif callable_value is value and not name.startswith("__"):
                yield name, _class_snapshot(value) if isinstance(value, type) else _snapshot(value)


def _class_snapshot(cls):
    if (module := _class_module(cls)) is None:
        return cls.__module__, cls.__qualname__
    with HMR_CONTEXT.untrack():
        return _class_signature(module, cls.__qualname__), tuple((base.__qualname__, tuple(_class_dependencies(base))) for base in cls.__mro__)


def _snapshot(value):
    if isinstance(value, (str, int, float, bool, bytes, type(None))):
        return value
    if isinstance(value, (FunctionType, MethodType, partial)):
        return callable_signature(value)
    if isinstance(value, dict):
        return {key: _snapshot(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_snapshot(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return type(value).__name__, sorted((_snapshot(item) for item in value), key=repr)
    if hasattr(value, "__dict__"):
        return type(value).__qualname__, tuple(sorted((name, _snapshot(item)) for name, item in vars(value).items()))
    slots = tuple(name for base in type(value).__mro__ for name in getattr(base, "__slots__", ()))
    if slots:
        return type(value).__qualname__, tuple((name, _snapshot(getattr(value, name))) for name in slots)
    return object()  # Unknown values must not silently compare equal after reload.


def _class_attribute_names(code: CodeType, cls, instance=None):
    instance = code.co_varnames[0] if instance is None and code.co_varnames else instance or "self"
    previous = None
    for instruction in get_instructions(code):
        if (
            instruction.opname in {"LOAD_ATTR", "LOAD_METHOD"}
            and previous is not None
            and (
                (previous.opname in {"LOAD_FAST", "LOAD_FAST_BORROW", "LOAD_DEREF"} and previous.argval == instance)
                or (previous.opname in {"LOAD_GLOBAL", "LOAD_NAME"} and previous.argval == cls.__name__)
            )
        ):
            yield instruction.argval
        previous = instruction
    for value in code.co_consts:
        if isinstance(value, CodeType):
            yield from _class_attribute_names(value, cls, instance)


def _implicit_dunder_names(code: CodeType):
    comparisons = {"==": "__eq__", "!=": "__ne__", "<": "__lt__", "<=": "__le__", ">": "__gt__", ">=": "__ge__"}
    operations = {"BINARY_SUBSCR": "__getitem__", "GET_ITER": "__iter__", "GET_LEN": "__len__", "CONTAINS_OP": "__contains__", "UNARY_NOT": "__bool__", "TO_BOOL": "__bool__"}
    for instruction in get_instructions(code):
        if instruction.opname == "COMPARE_OP" and (operator := instruction.argrepr.removeprefix("bool(").removesuffix(")")) in comparisons:
            yield comparisons[operator]
        if instruction.opname in operations:
            yield operations[instruction.opname]
        if instruction.opname == "BINARY_OP" and instruction.argrepr == "[]":
            yield "__getitem__"
        if instruction.opname == "CALL":
            yield "__call__"
    for value in code.co_consts:
        if isinstance(value, CodeType):
            yield from _implicit_dunder_names(value)


def _reachable_class_members(cls, obj):
    attributes, helpers, seen = set(), [], set()
    # Iterating builtins such as list(self) do not expose GET_ITER to the caller's bytecode.
    implicit = {"__init__", "__new__", "__bool__", "__len__", "__iter__"}
    pending = [obj, *(value for name in implicit if (value := _unwrap_descriptor(getattr_static(cls, name, None))) is not None and _is_callable(value))]
    attributes.update(implicit)
    while pending:
        value = pending.pop()
        if id(value) in seen:
            continue
        seen.add(id(value))
        helpers.append(value)
        for func in _callable_chain(value):
            if not isinstance(func, FunctionType):
                continue
            attributes_found = set(_class_attribute_names(func.__code__, cls))
            names = attributes_found | set(_implicit_dunder_names(func.__code__))
            if attributes_found:
                names |= {"__getattr__", "__getattribute__"}
            for name in names:
                if name.startswith("test"):
                    continue
                attributes.add(name)
                if (base := next((base for base in cls.__mro__ if name in vars(base)), None)) is not None and _is_callable(helper := _unwrap_descriptor(vars(base)[name])):
                    pending.append(helper)
    return attributes, helpers


def track_callable_globals(obj, seen=None):
    seen = set() if seen is None else seen
    if id(obj) in seen:
        return
    seen.add(id(obj))
    for target in _callable_chain(obj):
        if not isinstance(target, FunctionType) or not (module := ReactiveModule.instances.get(Path(target.__code__.co_filename).resolve())):
            continue
        names = tuple(set(_global_names(target.__code__)) - set(target.__code__.co_freevars))
        track_global_names(module, (name for name in names if not _is_callable(vars(module).get(name)) and not isinstance(vars(module).get(name), type)))
        for name in names:
            if _is_callable(value := vars(module).get(name)):
                track_callable_globals(value, seen)


@dataclass(frozen=True)
class TestRef:
    module: str
    name: str
    method: str | None = None
    fixture_values: Callable = lambda _: {}

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
        with HMR_CONTEXT.untrack():
            cls = getattr(import_module(self.module), self.name)
            obj = cls
            if self.method:
                obj = getattr(obj, self.method)
                attributes, _ = _reachable_class_members(cls, obj)
            fixtures = tuple((name, callable_signature(fixture)) for name, fixture in self.fixture_values(obj).items())
            return callable_signature(obj), fixtures, (tuple(_class_dependencies(cls, attributes)),) if self.method else ()

    def track_globals(self, func):
        track_callable_globals(func)
        if self.method:
            module = import_module(self.module)
            cls = module.__dict__[self.name] if isinstance(module, ReactiveModule) else getattr(module, self.name)
            _, helpers = _reachable_class_members(cls, func)
            for helper in helpers:
                track_callable_globals(helper)
        for fixture in self.fixture_values(func).values():
            track_callable_globals(fixture)


def collect_module(module_name: str, fixture_values=lambda _: {}):
    module = import_module(module_name)
    if isinstance(module, ReactiveModule):
        load(module)
        names = ReactiveModule.__dir__(module)
    else:
        names = vars(module)
    for name in names:
        if name.startswith("test") and callable(getattr(module, name)):
            yield TestRef(module_name, name, fixture_values=fixture_values)
        elif name.startswith("Test") and isclass(obj := getattr(module, name)):
            for method_name in dir(obj):
                if method_name.startswith("test") and callable(getattr(obj, method_name)):
                    yield TestRef(module_name, name, method_name, fixture_values)


class ReactiveCollector:
    def __init__(self, run: Callable[[Callable[[], Any]], Any], fixture_values=lambda _: {}):
        self.run = run
        self.fixture_values = fixture_values
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
