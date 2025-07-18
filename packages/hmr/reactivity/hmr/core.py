import sys
from ast import get_docstring, parse
from collections.abc import Iterable, MutableMapping, Sequence
from contextlib import suppress
from functools import cached_property, partial
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from importlib.util import spec_from_loader
from inspect import currentframe, ismethod
from os import getenv
from pathlib import Path
from site import getsitepackages, getusersitepackages
from sysconfig import get_paths
from types import ModuleType, TracebackType
from typing import Self
from weakref import WeakValueDictionary

from ..context import Context
from ..helpers import DerivedMethod
from ..primitives import BaseDerived, Derived, Signal
from ._common import HMR_CONTEXT
from .fs import notify, setup_fs_audithook
from .hooks import call_post_reload_hooks, call_pre_reload_hooks
from .proxy import Proxy


def is_called_internally(*, extra_depth=0) -> bool:
    """Protect private methods from being called from outside this package."""

    frame = currentframe()  # this function
    assert frame is not None

    for _ in range(extra_depth + 2):
        frame = frame.f_back
        assert frame is not None

    return frame.f_globals.get("__package__") == __package__


class Name(Signal, BaseDerived):
    pass


class NamespaceProxy(Proxy):
    def __init__(self, initial: MutableMapping, module: "ReactiveModule", check_equality=True, *, context: Context | None = None):
        super().__init__(initial, check_equality, context=context)
        self.module = module

    def _null(self):
        self.module.load.subscribers.add(signal := Name(self.UNSET, self._check_equality, context=self.context))
        signal.dependencies.add(self.module.load)
        return signal

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        finally:
            signal = self._signals[key]
            if self.module.load in signal.subscribers:
                # a module's loader shouldn't subscribe its variables
                signal.subscribers.remove(self.module.load)
                self.module.load.dependencies.remove(signal)


STATIC_ATTRS = frozenset(("__path__", "__dict__", "__spec__", "__name__", "__file__", "__loader__", "__package__", "__cached__"))


class ReactiveModule(ModuleType):
    instances: WeakValueDictionary[Path, Self] = WeakValueDictionary()

    def __init__(self, file: Path, namespace: dict, name: str, doc: str | None = None):
        super().__init__(name, doc)
        self.__is_initialized = False
        self.__dict__.update(namespace)
        self.__is_initialized = True

        self.__namespace = namespace
        self.__namespace_proxy = NamespaceProxy(namespace, self, context=HMR_CONTEXT)
        self.__file = file

        __class__.instances[file.resolve()] = self

    @property
    def file(self):
        if is_called_internally(extra_depth=1):  # + 1 for `__getattribute__`
            return self.__file
        raise AttributeError("file")

    @partial(DerivedMethod, context=HMR_CONTEXT)
    def __load(self):
        try:
            file = self.__file
            ast = parse(file.read_text("utf-8"), str(file))
            code = compile(ast, str(file), "exec", dont_inherit=True)
        except SyntaxError as e:
            sys.excepthook(type(e), e, e.__traceback__)
        else:
            self.__doc__ = get_docstring(ast)
            exec(code, self.__namespace, self.__namespace_proxy)  # https://github.com/python/cpython/issues/121306
            self.__namespace_proxy.update(self.__namespace)
        finally:
            load = self.__load
            assert ismethod(load.fn)  # for type narrowing
            for dep in list(load.dependencies):
                if isinstance(dep, Derived) and ismethod(dep.fn) and isinstance(dep.fn.__self__, ReactiveModule) and dep.fn.__func__ is load.fn.__func__:
                    # unsubscribe it because we want invalidation to be fine-grained
                    dep.subscribers.remove(load)
                    load.dependencies.remove(dep)

    @property
    def load(self):
        if is_called_internally(extra_depth=1):  # + 1 for `__getattribute__`
            return self.__load
        raise AttributeError("load")

    def __dir__(self):
        return iter(self.__namespace_proxy)

    def __getattribute__(self, name: str):
        if name == "__dict__" and self.__is_initialized:
            return self.__namespace
        if name == "instances":  # class-level attribute
            raise AttributeError(name)
        return super().__getattribute__(name)

    def __getattr__(self, name: str):
        try:
            return self.__namespace_proxy[name] if name not in STATIC_ATTRS else self.__namespace[name]
        except KeyError as e:
            if name not in STATIC_ATTRS and (getattr := self.__namespace_proxy.get("__getattr__")):
                return getattr(name)
            raise AttributeError(*e.args) from None

    def __setattr__(self, name: str, value):
        if is_called_internally():
            return super().__setattr__(name, value)
        self.__namespace_proxy[name] = value


class ReactiveModuleLoader(Loader):
    def create_module(self, spec: ModuleSpec):
        assert spec.origin is not None, "This loader can only load file-backed modules"
        path = Path(spec.origin)
        namespace = {"__file__": spec.origin, "__spec__": spec, "__loader__": self, "__name__": spec.name, "__package__": spec.parent, "__cached__": None}
        if spec.submodule_search_locations is not None:
            namespace["__path__"] = spec.submodule_search_locations[:] = [str(path.parent)]
        return ReactiveModule(path, namespace, spec.name)

    def exec_module(self, module: ModuleType):
        assert isinstance(module, ReactiveModule)
        module.load()


_loader = ReactiveModuleLoader()  # This is a singleton loader instance used by the finder


def _deduplicate(input_paths: Iterable[str | Path]):
    paths = [*{Path(p).resolve(): None for p in input_paths}]  # dicts preserve insertion order
    for i, p in enumerate(s := sorted(paths, reverse=True), start=1):
        if is_relative_to_any(p, s[i:]):
            paths.remove(p)
    return paths


class ReactiveModuleFinder(MetaPathFinder):
    def __init__(self, includes: Iterable[str] = ".", excludes: Iterable[str] = ()):
        super().__init__()
        builtins = map(get_paths().__getitem__, ("stdlib", "platstdlib", "platlib", "purelib"))
        self.includes = _deduplicate(includes)
        self.excludes = _deduplicate((*([venv] if (venv := getenv("VIRTUAL_ENV")) else ()), *getsitepackages(), getusersitepackages(), *builtins, *excludes))

        self._last_sys_path: list[str] = []
        self._last_cwd: Path = Path()
        self._cached_search_paths: list[Path] = []

    def _accept(self, path: Path):
        return path.is_file() and not is_relative_to_any(path, self.excludes) and is_relative_to_any(path, self.includes)

    @property
    def search_paths(self):
        # Currently we assume `includes` and `excludes` never change

        if sys.path == self._last_sys_path and self._last_cwd.exists() and Path.cwd().samefile(self._last_cwd):
            return self._cached_search_paths

        res = [path for path in (Path(p).resolve() for p in sys.path) if not is_relative_to_any(path, self.excludes) and any(i.is_relative_to(path) or path.is_relative_to(i) for i in self.includes)]

        self._cached_search_paths = res
        self._last_cwd = Path.cwd()
        self._last_sys_path = [*sys.path]
        return res

    def find_spec(self, fullname: str, paths: Sequence[str] | None, _=None):
        if fullname in sys.modules:
            return None

        for directory in self.search_paths:
            if directory.is_file():
                continue

            file = directory / f"{fullname.replace('.', '/')}.py"
            if self._accept(file) and (paths is None or is_relative_to_any(file, paths)):
                return spec_from_loader(fullname, _loader, origin=str(file))
            file = directory / f"{fullname.replace('.', '/')}/__init__.py"
            if self._accept(file) and (paths is None or is_relative_to_any(file, paths)):
                return spec_from_loader(fullname, _loader, origin=str(file), is_package=True)


def is_relative_to_any(path: Path, paths: Iterable[str | Path]):
    return any(path.is_relative_to(p) for p in paths)


def patch_module(name_or_module: str | ModuleType):
    name = name_or_module if isinstance(name_or_module, str) else name_or_module.__name__
    module = sys.modules[name_or_module] if isinstance(name_or_module, str) else name_or_module
    assert isinstance(module.__file__, str), f"{name} is not a file-backed module"
    m = sys.modules[name] = ReactiveModule(Path(module.__file__), module.__dict__, module.__name__, module.__doc__)
    return m


def patch_meta_path(includes: Iterable[str] = (".",), excludes: Iterable[str] = ()):
    sys.meta_path.insert(0, ReactiveModuleFinder(includes, excludes))


def get_path_module_map():
    return {**ReactiveModule.instances}


class ErrorFilter:
    def __init__(self, *exclude_filenames: str):
        self.exclude_filenames = set(exclude_filenames)

    def __call__(self, tb: TracebackType):
        current = tb
        while current is not None:
            if current.tb_frame.f_code.co_filename not in self.exclude_filenames:
                return current
            current = current.tb_next
        return tb

    def __enter__(self):
        return self

    def __exit__(self, exc_type: type[BaseException], exc_value: BaseException, traceback: TracebackType):
        if exc_value is None:
            return
        tb = self(traceback)
        exc_value = exc_value.with_traceback(tb)
        sys.excepthook(exc_type, exc_value, tb)
        return True


class BaseReloader:
    def __init__(self, entry_file: str, includes: Iterable[str] = (".",), excludes: Iterable[str] = ()):
        self.entry = entry_file
        self.includes = includes
        self.excludes = excludes
        patch_meta_path(includes, excludes)
        self.error_filter = ErrorFilter(*map(str, Path(__file__, "../..").resolve().glob("**/*.py")))
        setup_fs_audithook()

    @cached_property
    def entry_module(self):
        namespace = {"__file__": self.entry, "__name__": "__main__"}
        return ReactiveModule(Path(self.entry), namespace, "__main__")

    def run_entry_file(self):
        with self.error_filter:
            self.entry_module.load()

    @property
    def watch_filter(self):
        from watchfiles import PythonFilter

        return PythonFilter(ignore_paths=tuple(self.excludes))

    def on_events(self, events: Iterable[tuple[int, str]]):
        from watchfiles import Change

        if not events:
            return

        path2module = get_path_module_map()
        staled_modules: set[ReactiveModule] = set()

        call_pre_reload_hooks()

        with HMR_CONTEXT.batch():
            for type, file in events:
                if type is not Change.deleted:
                    path = Path(file).resolve()
                    if module := path2module.get(path):
                        staled_modules.add(module)
                    else:
                        notify(path)

            for module in staled_modules:
                with self.error_filter:
                    module.load.invalidate()
                    module.load()  # because `module.load` is not pulled by anyone

        call_post_reload_hooks()


class _SimpleEvent:
    def __init__(self):
        self._set = False

    def set(self):
        self._set = True

    def is_set(self):
        return self._set


class SyncReloader(BaseReloader):
    @cached_property
    def _stop_event(self):
        return _SimpleEvent()

    def stop_watching(self):
        self._stop_event.set()

    def start_watching(self):
        from watchfiles import watch

        for events in watch(self.entry, *self.includes, stop_event=self._stop_event):
            self.on_events(events)

        del self._stop_event

    def keep_watching_until_interrupt(self):
        call_pre_reload_hooks()
        with suppress(KeyboardInterrupt), HMR_CONTEXT.effect(self.run_entry_file):
            call_post_reload_hooks()
            self.start_watching()


class AsyncReloader(BaseReloader):
    @cached_property
    def _stop_event(self):
        from asyncio import Event

        return Event()

    def stop_watching(self):
        self._stop_event.set()

    async def start_watching(self):
        from watchfiles import awatch

        async for events in awatch(self.entry, *self.includes, stop_event=self._stop_event):
            self.on_events(events)

        del self._stop_event

    async def keep_watching_until_interrupt(self):
        call_pre_reload_hooks()
        with suppress(KeyboardInterrupt), HMR_CONTEXT.effect(self.run_entry_file):
            call_post_reload_hooks()
            await self.start_watching()


def cli():
    if len(sys.argv) < 2:
        print("\n Usage: hmr <entry file>, just like python <entry file>\n")
        exit(1)
    sys.argv.pop(0)  # this file itself
    entry = sys.argv[0]
    if not (path := Path(entry)).is_file():
        raise FileNotFoundError(path.resolve())
    sys.path.insert(0, str(path.parent.resolve()))
    reloader = SyncReloader(entry)
    sys.modules["__main__"] = reloader.entry_module
    reloader.keep_watching_until_interrupt()


__version__ = "0.6.4.4"
