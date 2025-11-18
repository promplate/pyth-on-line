import builtins
import sys
from ast import get_docstring, parse
from collections.abc import Callable, Iterable, MutableMapping, Sequence
from contextlib import suppress
from functools import cached_property
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from inspect import ismethod
from os import getenv
from pathlib import Path
from site import getsitepackages, getusersitepackages
from sysconfig import get_paths
from types import ModuleType, TracebackType
from typing import Any, Self
from weakref import WeakValueDictionary

from . import post_reload
from .. import derived_method
from ..context import Context
from ..primitives import BaseDerived, Derived, Signal
from ._common import HMR_CONTEXT
from .fs import add_filter, notify, setup_fs_audithook
from .hooks import call_post_reload_hooks, call_pre_reload_hooks
from .proxy import Proxy


def is_called_internally(*, extra_depth=0) -> bool:
    """Protect private methods from being called from outside this package."""
    frame = sys._getframe(extra_depth + 2)  # noqa: SLF001
    return frame.f_globals.get("__package__") == __package__


class Name(Signal, BaseDerived):
    def get(self, track=True):
        self._sync_dirty_deps()
        return super().get(track)


class NamespaceProxy(Proxy):
    def __init__(self, initial: MutableMapping, module: "ReactiveModule", check_equality=True, *, context: Context | None = None):
        self.module = module
        super().__init__(initial, check_equality, context=context)

    def _signal(self, value=False):
        self.module.load.subscribers.add(signal := Name(value, self._check_equality, context=self.context))
        signal.dependencies.add(self.module.load)
        return signal

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        finally:
            signal = self._keys[key]
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
        self.__hooks: list[Callable[[], Any]] = []
        self.__file = file

        __class__.instances[file.resolve()] = self

    @property
    def file(self):
        if is_called_internally(extra_depth=1):  # + 1 for `__getattribute__`
            return self.__file
        raise AttributeError("file")

    @property
    def register_dispose_callback(self):
        if is_called_internally(extra_depth=1):  # + 1 for `__getattribute__`
            return self.__hooks.append
        raise AttributeError("register_dispose_callback")

    @derived_method(context=HMR_CONTEXT)
    def __load(self):
        try:
            file = self.__file
            # logger.info(f"  Reading file: {file}")
            file_text = file.read_text("utf-8")
            if "pytest.console_main()" in file_text:
                file_text = file_text.replace("raise SystemExit(pytest.console_main())", "pytest.console_main()")

            ast = parse(file_text, str(file))
            code = compile(ast, str(file), "exec", dont_inherit=True)
            self.__flags = code.co_flags
        except SyntaxError as e:
            sys.excepthook(type(e), e, e.__traceback__)
        else:
            for dispose in self.__hooks:
                with suppress(Exception):
                    dispose()
            self.__hooks.clear()
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
        namespace = {"__file__": spec.origin, "__spec__": spec, "__loader__": self, "__name__": spec.name, "__package__": spec.parent, "__cached__": None, "__builtins__": __builtins__}
        if spec.submodule_search_locations is not None:
            namespace["__path__"] = spec.submodule_search_locations[:] = [str(path.parent)]
        return ReactiveModule(path, namespace, spec.name)

    def exec_module(self, module: ModuleType):
        assert isinstance(module, ReactiveModule)
        module.load()


_loader = ReactiveModuleLoader()  # This is a singleton loader instance used by the finder


def _deduplicate(input_paths: Iterable[str | Path | None]):
    paths = [*{Path(p).resolve(): None for p in input_paths if p is not None}]  # dicts preserve insertion order
    for i, p in enumerate(s := sorted(paths, reverse=True), start=1):
        if is_relative_to_any(p, s[i:]):
            paths.remove(p)
    return paths


class ReactiveModuleFinder(MetaPathFinder):
    def __init__(self, includes: Iterable[str] = ".", excludes: Iterable[str] = ()):
        super().__init__()
        builtins = map(get_paths().__getitem__, ("stdlib", "platstdlib", "platlib", "purelib"))
        self.includes = _deduplicate(includes)
        self.excludes = _deduplicate((getenv("VIRTUAL_ENV"), *getsitepackages(), getusersitepackages(), *builtins, *excludes))
        setup_fs_audithook()
        add_filter(lambda path: not is_relative_to_any(path, self.excludes) and is_relative_to_any(path, self.includes))

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

        res = [
            path
            for path in (Path(p).resolve() for p in sys.path)
            if not path.is_file() and not is_relative_to_any(path, self.excludes) and any(i.is_relative_to(path) or path.is_relative_to(i) for i in self.includes)
        ]

        self._cached_search_paths = res
        self._last_cwd = Path.cwd()
        self._last_sys_path = [*sys.path]
        return res

    def find_spec(self, fullname: str, paths: Sequence[str | Path] | None, _=None):
        if fullname in sys.modules:
            return None

        if paths is not None:
            paths = [path.resolve() for path in (Path(p) for p in paths) if path.is_dir()]

        for directory in self.search_paths:
            file = directory / f"{fullname.replace('.', '/')}.py"
            if self._accept(file) and (paths is None or is_relative_to_any(file, paths)):
                return ModuleSpec(fullname, _loader, origin=str(file))
            file = directory / f"{fullname.replace('.', '/')}/__init__.py"
            if self._accept(file) and (paths is None or is_relative_to_any(file, paths)):
                return ModuleSpec(fullname, _loader, origin=str(file), is_package=True)


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
        current = last = tb
        first = None
        while current is not None:
            if current.tb_frame.f_code.co_filename not in self.exclude_filenames:
                if first is None:
                    first = current
                else:
                    last.tb_next = current
                last = current
            current = current.tb_next
        return first or tb

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
        self.error_filter = ErrorFilter(*map(str, Path(__file__, "../..").resolve().glob("**/*.py")), "<frozen importlib._bootstrap>")

    @cached_property
    def entry_module(self):
        spec = ModuleSpec("__main__", _loader, origin=self.entry)
        assert spec is not None
        namespace = {"__file__": self.entry, "__name__": "__main__", "__spec__": spec, "__loader__": _loader, "__package__": spec.parent, "__cached__": None, "__builtins__": builtins}
        return ReactiveModule(Path(self.entry), namespace, "__main__")

    def run_entry_file(self):
        with self.error_filter:
            self.entry_module.load()

    def on_events(self, events: Iterable[tuple[int, str]]):
        from watchfiles import Change

        if not events:
            return

        self.on_changes({Path(file).resolve() for type, file in events if type is not Change.deleted})

    def on_changes(self, files: set[Path]):
        path2module = get_path_module_map()

        call_pre_reload_hooks()

        with self.error_filter, HMR_CONTEXT.batch():
            for path in files:
                if module := path2module.get(path):
                    module.load.invalidate()
                else:
                    notify(path)

        self.entry_module.load.invalidate()

        call_post_reload_hooks()

    @cached_property
    def _stop_event(self):
        return _SimpleEvent()

    def stop_watching(self):
        self._stop_event.set()


class _SimpleEvent:
    def __init__(self):
        self._set = False

    def set(self):
        self._set = True

    def is_set(self):
        return self._set


class SyncReloader(BaseReloader):
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


# class AsyncReloader(BaseReloader):
#     async def start_watching(self):
#         from watchfiles import awatch
#
#         async for events in awatch(self.entry, *self.includes, stop_event=self._stop_event):  # type: ignore
#             self.on_events(events)
#
#         del self._stop_event
#
#     async def keep_watching_until_interrupt(self):
#         call_pre_reload_hooks()
#         with suppress(KeyboardInterrupt), HMR_CONTEXT.effect(self.run_entry_file):
#             call_post_reload_hooks()
#             await self.start_watching()


import logging
#
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger("hmr.debug")

from reactivity.hmr.hooks import pre_reload

import logging
import sys
from pathlib import Path

import asyncio
import ctypes
import logging
import threading
from contextlib import suppress
import signal


# logger = logging.getLogger("hmr.debug")


@pre_reload
def clear_pytest_cache():
    """Clear pytest cache between reloads"""
    import importlib
    import gc

    pytest_modules = [
        k for k in list(sys.modules.keys())
        if k.startswith('_pytest')
        or k.startswith('test_') or '.test_' in k or k.endswith('_test')
        or k == "anyio"
        or k == "pytest_asyncio"
    ]

    # logger.info(f"Clearing {len(pytest_modules)} pytest modules")

    for mod in pytest_modules:
        try:
            del sys.modules[mod]
        except KeyError:
            pass

    gc.collect()
    importlib.invalidate_caches()


import asyncio
import ctypes
import logging
import threading
from contextlib import suppress
from pathlib import Path

logger = logging.getLogger("hmr.debug")


class AsyncReloader(BaseReloader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._execution_thread = None
        self._run_count = 0

    def _kill_thread(self):
        """Kill execution thread and wait for it to die"""
        if not self._execution_thread:
            logger.info("No execution thread to kill")
            return

        if not self._execution_thread.is_alive():
            logger.info("Execution thread already dead")
            return

        thread_id = self._execution_thread.ident
        logger.info(f"⚠️  Interrupting thread {thread_id}...")

        try:
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(thread_id),
                ctypes.py_object(SystemExit)
            )

            if res > 0:
                self._execution_thread.join(timeout=2.0)
                if self._execution_thread.is_alive():
                    logger.warning("⚠️  Thread still alive after 2s")
                else:
                    logger.info("✓ Thread killed successfully")
        except Exception as e:
            logger.error(f"Kill failed: {e}")

    def _run_tests(self):
        """Run tests in current thread"""
        self._run_count += 1
        logger.info(f"\n{'#'*80}")
        logger.info(f"▶️  EXECUTION #{self._run_count}")
        logger.info(f"{'#'*80}\n")

        try:
            self.run_entry_file()
            logger.info("✅ Completed")
        except KeyboardInterrupt:
            logger.info("⏹️  Interrupted")
        except SystemExit:
            pass
        except Exception as e:
            logger.error(f"❌ Error: {e}")

    def on_changes(self, files: set):
        """Override to prevent notify() from triggering effect"""
        from .core import get_path_module_map
        from .hooks import call_pre_reload_hooks

        path2module = get_path_module_map()
        call_pre_reload_hooks()

        # Only invalidate, don't notify!
        # notify() would trigger the effect synchronously
        with self.error_filter, HMR_CONTEXT.batch():
            for path in files:
                if module := path2module.get(path):
                    logger.info(f"Invalidating module: {path.name}")
                    module.load.invalidate()
                else:
                    # DON'T call notify(path) - that would trigger the effect!
                    # Just invalidate the entry module
                    logger.info(f"File changed: {path.name}")

            # Invalidate entry module so it reloads on next run
            logger.info("Invalidating entry module")
            self.entry_module.load.invalidate()

    async def start_watching(self):
        from watchfiles import awatch

        async for events in awatch(self.entry, *self.includes, stop_event=self._stop_event):
            logger.info(f"\n{'='*80}")
            logger.info(f"🔄 FILE CHANGE!")
            logger.info(f"{'='*80}")

            # Kill current execution
            self._kill_thread()

            # Process changes (invalidate only, no notify)
            files = {Path(file).resolve() for _, file in events}
            self.on_changes(files)

            # Start new execution immediately
            logger.info("🚀 Starting new execution...")
            self._execution_thread = threading.Thread(
                target=self._run_tests,
                daemon=True
            )
            self._execution_thread.start()

        del self._stop_event

    async def keep_watching_until_interrupt(self):
        from .hooks import call_pre_reload_hooks, call_post_reload_hooks

        call_pre_reload_hooks()

        # NO effect! We don't want the effect system involved at all
        # The file tracking happens naturally when run_entry_file executes
        call_post_reload_hooks()

        # Start initial execution
        logger.info("🚀 Starting initial execution...")
        self._execution_thread = threading.Thread(
            target=self._run_tests,
            daemon=True
        )
        self._execution_thread.start()

        # Start watching
        try:
            await self.start_watching()
        except KeyboardInterrupt:
            logger.info("\n👋 Stopping...")
            self._kill_thread()


__version__ = "0.7.6"
