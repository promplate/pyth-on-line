import sys
from collections.abc import Iterable, MutableMapping, Sequence
from contextlib import suppress
from functools import cached_property
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from importlib.util import spec_from_loader
from inspect import currentframe
from pathlib import Path
from runpy import run_path
from types import ModuleType

from . import Reactive, batch, create_effect, memoized_method


def is_called_in_this_file() -> bool:
    frame = currentframe()  # this function
    assert frame is not None

    frame = frame.f_back  # the function calling this function
    assert frame is not None

    frame = frame.f_back  # the function calling the function calling this function
    assert frame is not None

    return frame.f_globals.get("__file__") == __file__


class NamespaceProxy(Reactive):
    def __init__(self, initial: MutableMapping, check_equality=True):
        super().__init__(initial, check_equality)
        self._original = initial

    def __setitem__(self, key, value):
        self._original[key] = value
        return super().__setitem__(key, value)

    def __delitem__(self, key):
        del self._original[key]
        return super().__delitem__(key)


class ReactiveModule(ModuleType):
    def __init__(self, file: Path, namespace: dict, name: str, doc: str | None = None):
        super().__init__(name, doc)
        self.__namespace = namespace
        self.__namespace_proxy = NamespaceProxy(namespace)
        self.__file = file

    @property
    def file(self):
        if is_called_in_this_file():
            return self.__file
        raise AttributeError("file")

    @property
    def load(self):
        if is_called_in_this_file():
            return lambda: exec(self.__file.read_text("utf-8"), self.__namespace, self.__namespace_proxy)
        raise AttributeError("load")

    def __getattr__(self, name: str):
        try:
            return self.__namespace_proxy[name]
        except KeyError as e:
            raise AttributeError(*e.args) from e

    def __setattr__(self, name: str, value):
        if is_called_in_this_file():
            return super().__setattr__(name, value)
        self.__namespace_proxy[name] = value


class ReactiveModuleLoader(Loader):
    def __init__(self, file: Path, is_package=False):
        super().__init__()
        self._file = file
        self._is_package = is_package

    def create_module(self, spec: ModuleSpec):
        namespace = {}
        if self._is_package:
            assert self._file.name == "__init__.py"
            namespace["__path__"] = [str(self._file.parent.parent)]
        return ReactiveModule(self._file, namespace, spec.name)

    def exec_module(self, module: ModuleType):
        assert isinstance(module, ReactiveModule)
        create_effect(lambda: module.load())


class ReactiveModuleFinder(MetaPathFinder):
    def __init__(self, includes: Iterable[str] = ".", excludes: Iterable[str] = ()):
        super().__init__()
        self.includes = [Path(i).resolve() for i in includes]
        self.excludes = [Path(e).resolve() for e in excludes]

    def find_spec(self, fullname: str, paths: Sequence[str] | None, _=None):
        if fullname in sys.modules:
            return None

        for p in paths or sys.path:
            directory = Path(p).resolve()
            if directory.is_file():
                continue
            if any(directory.is_relative_to(exclude) for exclude in self.excludes):
                continue
            if all(not directory.is_relative_to(include) for include in self.includes):
                continue

            file = directory / f"{fullname.replace('.', '/')}.py"
            if file.is_file() and all(not file.is_relative_to(exclude) for exclude in self.excludes):
                return spec_from_loader(fullname, ReactiveModuleLoader(file), origin=str(file))
            file = directory / f"{fullname.replace('.', '/')}/__init__.py"
            if file.is_file() and all(not file.is_relative_to(exclude) for exclude in self.excludes):
                return spec_from_loader(fullname, ReactiveModuleLoader(file, is_package=True), origin=str(file), is_package=True)


def patch_module(name_or_module: str | ModuleType):
    name = name_or_module if isinstance(name_or_module, str) else name_or_module.__name__
    module = sys.modules[name_or_module] if isinstance(name_or_module, str) else name_or_module
    assert isinstance(module.__file__, str), f"{name} is not a file-backed module"
    m = sys.modules[name] = ReactiveModule(Path(module.__file__), module.__dict__, module.__name__, module.__doc__)
    return m


def patch_meta_path(includes: Iterable[str] = (".",), excludes: Iterable[str] = (".venv",)):
    sys.meta_path.insert(0, ReactiveModuleFinder(includes, excludes))


def get_path_module_map():
    return {module.file.resolve(): module for module in sys.modules.values() if isinstance(module, ReactiveModule)}


class BaseReloader:
    def __init__(self, entry_file: str, includes: Iterable[str] = (".",), excludes: Iterable[str] = ()):
        self.entry = entry_file
        self.includes = includes
        self.excludes = excludes
        patch_meta_path(includes, excludes)

    @memoized_method
    def run_entry_file(self):
        try:
            run_path(self.entry, run_name="__main__")
        except Exception as e:
            sys.excepthook(e.__class__, e, e.__traceback__)

    @property
    def watch_filter(self):
        from watchfiles import PythonFilter

        return PythonFilter(ignore_paths=tuple(self.excludes))

    def on_events(self, events: Iterable[tuple[int, str]]):
        from watchfiles import Change

        if not events:
            return

        path2module = get_path_module_map()

        with batch():
            for type, file in events:
                if type is Change.modified:
                    path = Path(file).resolve()
                    if path.samefile(self.entry):
                        self.run_entry_file.trigger()
                    elif module := path2module.get(path):
                        try:
                            module.load()
                        except Exception as e:
                            sys.excepthook(e.__class__, e, e.__traceback__)
            self.run_entry_file()


class SyncReloader(BaseReloader):
    @cached_property
    def _stop_event(self):
        from threading import Event

        return Event()

    def stop_watching(self):
        self._stop_event.set()
        del self._stop_event

    def start_watching(self):
        from watchfiles import watch

        for events in watch(self.entry, *self.includes, watch_filter=self.watch_filter, stop_event=self._stop_event):
            self.on_events(events)

    def keep_watching_until_interrupt(self):
        with suppress(KeyboardInterrupt):
            self.run_entry_file()
            self.start_watching()
        self.run_entry_file.dispose()


class AsyncReloader(BaseReloader):
    @cached_property
    def _stop_event(self):
        from asyncio import Event

        return Event()

    def stop_watching(self):
        self._stop_event.set()
        del self._stop_event

    async def start_watching(self):
        from watchfiles import awatch

        async for events in awatch(self.entry, *self.includes, watch_filter=self.watch_filter, stop_event=self._stop_event):
            self.on_events(events)

    async def keep_watching_until_interrupt(self):
        with suppress(KeyboardInterrupt):
            self.run_entry_file()
            await self.start_watching()
        self.run_entry_file.dispose()


def cli():
    if len(sys.argv) < 2:
        print("\n Usage: hmr <entry file>, just like python <entry file>\n")
        exit(1)
    entry = sys.argv[-1]
    assert Path(entry).is_file(), f"{entry} is not a file"
    sys.path.insert(0, ".")
    SyncReloader(entry, excludes={".venv"}).keep_watching_until_interrupt()


__version__ = "0.0.2.2"
