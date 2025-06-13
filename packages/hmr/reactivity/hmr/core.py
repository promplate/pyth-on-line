import sys
from collections.abc import Iterable, MutableMapping, Sequence
from contextlib import suppress
from functools import cached_property, partial
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from importlib.util import spec_from_loader
from inspect import currentframe, ismethod
from pathlib import Path
from site import getsitepackages
from types import ModuleType, TracebackType
from typing import Self
from weakref import WeakValueDictionary

from ..context import Context, new_context
from ..helpers import DerivedMethod
from ..primitives import BaseDerived, Derived, Signal
from .hooks import call_post_reload_hooks, call_pre_reload_hooks
from .proxy import Proxy


def is_called_internally(*, extra_depth=0) -> bool:
    """
    Determines if the caller is within the same package as this code.
    
    Args:
        extra_depth: Additional stack frames to skip when checking the caller.
    
    Returns:
        True if the caller's global package matches the current package; otherwise, False.
    """

    frame = currentframe()  # this function
    assert frame is not None

    for _ in range(extra_depth + 2):
        frame = frame.f_back
        assert frame is not None

    return frame.f_globals.get("__package__") == __package__


class Name(Signal, BaseDerived):
    pass


HMR_CONTEXT = new_context()


class NamespaceProxy(Proxy):
    def __init__(self, initial: MutableMapping, module: "ReactiveModule", check_equality=True, *, context: Context | None = None):
        """
        Initializes the NamespaceProxy with a namespace mapping, associated ReactiveModule, and optional context.
        
        Args:
            initial: The initial namespace mapping to wrap.
            module: The ReactiveModule instance this proxy is associated with.
            check_equality: Whether to check for value equality before updating signals.
            context: Optional reactive context for signal tracking.
        """
        super().__init__(initial, check_equality, context=context)
        self.module = module

    def _null(self):
        """
        Creates a new reactive signal linked to the module's load signal.
        
        Returns:
            A `Name` signal instance that depends on the module's load signal.
        """
        self.module.load.subscribers.add(signal := Name(self.UNSET, self._check_equality, context=self.context))
        signal.dependencies.add(self.module.load)
        return signal

    def __getitem__(self, key):
        """
        Retrieves an item from the proxied namespace and ensures the module's load signal does not subscribe to the variable's signal.
        
        Removes the module's load signal from the variable's signal subscribers to prevent self-subscription and redundant invalidation.
        """
        try:
            return super().__getitem__(key)
        finally:
            signal = self._signals[key]
            if self.module.load in signal.subscribers:
                # a module's loader shouldn't subscribe its variables
                signal.subscribers.remove(self.module.load)
                self.module.load.dependencies.remove(signal)


class ReactiveModule(ModuleType):
    instances: WeakValueDictionary[Path, Self] = WeakValueDictionary()

    def __init__(self, file: Path, namespace: dict, name: str, doc: str | None = None):
        """
        Initializes a ReactiveModule with the given file path, namespace, and name.
        
        Creates a proxy for the module's namespace to enable reactive tracking and registers the module instance for hot reloading.
        """
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
        """
        Returns the file path of the module if accessed internally.
        
        Raises:
            AttributeError: If accessed from outside the internal context.
        """
        if is_called_internally(extra_depth=1):  # + 1 for `__getattribute__`
            return self.__file
        raise AttributeError("file")

    @partial(DerivedMethod, context=HMR_CONTEXT)
    def __load(self):
        """
        Compiles and executes the module's source code within its reactive namespace.
        
        If a syntax error occurs during compilation, the exception is passed to the system exception hook. After execution, cleans up subscriptions to ensure fine-grained invalidation of dependencies.
        """
        try:
            code = compile(self.__file.read_text("utf-8"), str(self.__file), "exec", dont_inherit=True)
        except SyntaxError as e:
            sys.excepthook(type(e), e, e.__traceback__)
        else:
            exec(code, self.__namespace, self.__namespace_proxy)  # https://github.com/python/cpython/issues/121306
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
        """
        Provides access to the module's internal load method if called from within the package.
        
        Raises:
            AttributeError: If accessed externally.
        """
        if is_called_internally(extra_depth=1):  # + 1 for `__getattribute__`
            return self.__load
        raise AttributeError("load")

    def __dir__(self):
        """
        Returns an iterator over the keys in the module's namespace proxy.
        
        This provides attribute names available on the reactive module for introspection tools.
        """
        return iter(self.__namespace_proxy)

    def __getattribute__(self, name: str):
        """
        Returns the module's namespace dictionary for `__dict__` after initialization; otherwise, delegates attribute access to the base class.
        """
        if name == "__dict__" and self.__is_initialized:
            return self.__namespace
        return super().__getattribute__(name)

    def __getattr__(self, name: str):
        """
        Retrieves an attribute from the module's namespace proxy.
        
        If the attribute is not found and the attribute name is not "__path__", attempts to call a custom `__getattr__` defined in the module's namespace. Raises `AttributeError` if the attribute cannot be resolved.
        """
        try:
            return self.__namespace_proxy[name]
        except KeyError as e:
            if name != "__path__" and (getattr := self.__namespace_proxy.get("__getattr__")):
                return getattr(name)
            raise AttributeError(*e.args) from None

    def __setattr__(self, name: str, value):
        """
        Sets an attribute on the module, restricting direct assignment to internal calls.
        
        If called externally, assigns the value to the module's namespace proxy to enable reactive tracking.
        """
        if is_called_internally():
            return super().__setattr__(name, value)
        self.__namespace_proxy[name] = value


class ReactiveModuleLoader(Loader):
    def __init__(self, file: Path):
        """
        Initializes the loader with the specified module file path.
        
        Args:
            file: The path to the Python module file to be loaded.
        """
        super().__init__()
        self._file = file

    def create_module(self, spec: ModuleSpec):
        """
        Creates a new ReactiveModule instance for the given module specification.
        
        Initializes the module's namespace with standard attributes and sets the `__path__`
        attribute for packages.
        """
        namespace = {"__file__": str(self._file), "__spec__": spec, "__loader__": self, "__name__": spec.name}
        if spec.submodule_search_locations is not None:
            assert self._file.name == "__init__.py"
            namespace["__path__"] = [str(self._file.parent)]
        return ReactiveModule(self._file, namespace, spec.name)

    def exec_module(self, module: ModuleType):
        """
        Executes the code of a reactive module by invoking its load method.
        
        Args:
            module: The ReactiveModule instance to execute.
        """
        assert isinstance(module, ReactiveModule)
        module.load()


class ReactiveModuleFinder(MetaPathFinder):
    def __init__(self, includes: Iterable[str] = ".", excludes: Iterable[str] = ()):
        """
        Initializes the finder with include and exclude path lists.
        
        Args:
            includes: Paths to include when searching for modules. Defaults to the current directory.
            excludes: Paths to exclude from module searching. Defaults to an empty tuple, plus site-packages directories.
        """
        super().__init__()
        self.includes = [Path(i).resolve() for i in includes]
        self.excludes = [Path(e).resolve() for e in (*excludes, *getsitepackages())]

    def _accept(self, path: Path):
        """
        Determines if a file path should be accepted for reactive loading.
        
        Returns True if the path is a file, is not excluded, and is within the included paths.
        """
        return path.is_file() and not is_relative_to_any(path, self.excludes) and is_relative_to_any(path, self.includes)

    def find_spec(self, fullname: str, paths: Sequence[str] | None, _=None):
        """
        Finds a module specification for a given module name if it corresponds to an accepted Python file or package.
        
        Returns a ModuleSpec with a ReactiveModuleLoader if the module file or package is found and accepted; otherwise, returns None.
        """
        if fullname in sys.modules:
            return None

        for p in sys.path:
            directory = Path(p).resolve()
            if directory.is_file():
                continue

            file = directory / f"{fullname.replace('.', '/')}.py"
            if self._accept(file) and (paths is None or is_relative_to_any(file, paths)):
                return spec_from_loader(fullname, ReactiveModuleLoader(file), origin=str(file))
            file = directory / f"{fullname.replace('.', '/')}/__init__.py"
            if self._accept(file) and (paths is None or is_relative_to_any(file, paths)):
                return spec_from_loader(fullname, ReactiveModuleLoader(file), origin=str(file), is_package=True)


def is_relative_to_any(path: Path, paths: Iterable[str | Path]):
    """
    Returns True if the given path is relative to any of the specified paths.
    
    Args:
        path: The path to check.
        paths: An iterable of paths to compare against.
    
    Returns:
        True if path is relative to at least one path in paths; otherwise, False.
    """
    return any(path.is_relative_to(p) for p in paths)


def patch_module(name_or_module: str | ModuleType):
    """
    Replaces a loaded module in sys.modules with a ReactiveModule for hot reloading.
    
    If given a module name or module object, wraps its file and namespace in a ReactiveModule,
    enabling reactive reloading on source changes. Returns the new ReactiveModule instance.
    
    Args:
        name_or_module: The name of the module or the module object to patch.
    
    Returns:
        The ReactiveModule instance replacing the original module.
    """
    name = name_or_module if isinstance(name_or_module, str) else name_or_module.__name__
    module = sys.modules[name_or_module] if isinstance(name_or_module, str) else name_or_module
    assert isinstance(module.__file__, str), f"{name} is not a file-backed module"
    m = sys.modules[name] = ReactiveModule(Path(module.__file__), module.__dict__, module.__name__, module.__doc__)
    return m


def patch_meta_path(includes: Iterable[str] = (".",), excludes: Iterable[str] = ()):
    """
    Inserts a ReactiveModuleFinder into sys.meta_path to enable reactive module loading.
    
    Args:
        includes: Paths to include for reactive module loading.
        excludes: Paths to exclude from reactive module loading.
    """
    sys.meta_path.insert(0, ReactiveModuleFinder(includes, excludes))


def get_path_module_map():
    """
    Returns a dictionary mapping file paths to their corresponding ReactiveModule instances.
    """
    return {**ReactiveModule.instances}


class ErrorFilter:
    def __init__(self, *exclude_filenames: str):
        """
        Initializes the ErrorFilter with a set of filenames to exclude from tracebacks.
        
        Args:
            *exclude_filenames: Filenames to be excluded from error tracebacks.
        """
        self.exclude_filenames = set(exclude_filenames)

    def __call__(self, tb: TracebackType):
        """
        Returns the first traceback frame not excluded by filename.
        
        Traverses the given traceback and returns the first frame whose filename is not in the exclusion list. If all frames are excluded, returns the original traceback.
        """
        current = tb
        while current is not None:
            if current.tb_frame.f_code.co_filename not in self.exclude_filenames:
                return current
            current = current.tb_next
        return tb

    def __enter__(self):
        """
        Enters the context manager and returns the ErrorFilter instance.
        """
        return self

    def __exit__(self, exc_type: type[BaseException], exc_value: BaseException, traceback: TracebackType):
        """
        Handles exceptions by filtering the traceback and invoking the system exception hook.
        
        If an exception occurs within the context, rewrites its traceback to exclude specified files
        and passes the filtered exception to `sys.excepthook`. Suppresses further propagation of the exception.
        """
        if exc_value is None:
            return
        tb = self(traceback)
        exc_value = exc_value.with_traceback(tb)
        sys.excepthook(exc_type, exc_value, tb)
        return True


class BaseReloader:
    def __init__(self, entry_file: str, includes: Iterable[str] = (".",), excludes: Iterable[str] = ()):
        """
        Initializes the base reloader with the entry file and path filters.
        
        Args:
            entry_file: Path to the entry Python file to run and reload.
            includes: Iterable of paths to include for hot reloading.
            excludes: Iterable of paths to exclude from hot reloading.
        """
        self.entry = entry_file
        self.includes = includes
        self.excludes = excludes
        patch_meta_path(includes, excludes)
        self.error_filter = ErrorFilter(*(str(i) for i in Path(__file__, "../..").resolve().glob("**/*.py")))

    @cached_property
    def entry_module(self):
        """
        Creates and returns a ReactiveModule instance for the entry file as the main module.
        
        The returned module uses the entry file path and a namespace with `__file__` and `__name__` set appropriately.
        """
        namespace = {"__file__": self.entry, "__name__": "__main__"}
        return ReactiveModule(Path(self.entry), namespace, "__main__")

    def run_entry_file(self):
        """
        Executes the entry module's code within the error filter context.
        
        Runs the entry module's reactive load method, ensuring that exceptions are filtered to exclude internal frames.
        """
        with self.error_filter:
            self.entry_module.load()

    @property
    def watch_filter(self):
        """
        Returns a Python file filter that ignores excluded paths.
        
        The filter is used to determine which files should be monitored for changes, excluding any paths specified in the reloader's `excludes` attribute.
        """
        from watchfiles import PythonFilter

        return PythonFilter(ignore_paths=tuple(self.excludes))

    def on_events(self, events: Iterable[tuple[int, str]]):
        """
        Handles file change events by reloading affected reactive modules.
        
        Identifies modules corresponding to changed files, invalidates their load signals, and reloads them within a reactive batch. Pre- and post-reload hooks are called before and after the reload process.
        """
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

            for module in staled_modules:
                with self.error_filter:
                    module.load.invalidate()
                    module.load()  # because `module.load` is not pulled by anyone

        call_post_reload_hooks()


class _SimpleEvent:
    def __init__(self):
        """
        Initializes the event flag in an unset state.
        """
        self._set = False

    def set(self):
        """
        Sets the event flag to indicate that the event has occurred.
        """
        self._set = True

    def is_set(self):
        """
        Checks whether the event flag is set.
        
        Returns:
            True if the event has been set, otherwise False.
        """
        return self._set


class SyncReloader(BaseReloader):
    @cached_property
    def _stop_event(self):
        """
        Returns a new instance of a simple event flag used to control stopping of the synchronous file watcher.
        """
        return _SimpleEvent()

    def stop_watching(self):
        """
        Signals the reloader to stop watching for file changes.
        """
        self._stop_event.set()

    def start_watching(self):
        """
        Starts synchronous file watching and triggers reloads on detected changes.
        
        Monitors the entry file and included paths for changes using a synchronous watcher. When file events are detected, calls `on_events` to handle reload logic. Stops watching when the stop event is set.
        """
        from watchfiles import watch

        for events in watch(self.entry, *self.includes, watch_filter=self.watch_filter, stop_event=self._stop_event):
            self.on_events(events)

        del self._stop_event

    def keep_watching_until_interrupt(self):
        """
        Runs the entry file with hot reloading enabled, watching for file changes until interrupted.
        
        This method executes pre-reload hooks, runs the entry file reactively, executes post-reload hooks, and starts synchronous file watching. The process continues until a keyboard interrupt is received.
        """
        call_pre_reload_hooks()
        with suppress(KeyboardInterrupt), HMR_CONTEXT.effect(self.run_entry_file):
            call_post_reload_hooks()
            self.start_watching()


class AsyncReloader(BaseReloader):
    @cached_property
    def _stop_event(self):
        """
        Returns a new asyncio.Event instance used to signal stopping of the asynchronous reloader.
        """
        from asyncio import Event

        return Event()

    def stop_watching(self):
        """
        Signals the reloader to stop watching for file changes.
        """
        self._stop_event.set()

    async def start_watching(self):
        """
        Asynchronously watches for file changes and triggers reload events.
        
        Monitors the entry file and included paths for changes using an asynchronous file watcher. When changes are detected, calls `on_events` with the set of file events. Stops watching when the stop event is set.
        """
        from watchfiles import awatch

        async for events in awatch(self.entry, *self.includes, watch_filter=self.watch_filter, stop_event=self._stop_event):
            self.on_events(events)

        del self._stop_event

    async def keep_watching_until_interrupt(self):
        """
        Runs the entry file reactively and starts asynchronous file watching until interrupted.
        
        This method executes pre-reload hooks, runs the entry file within a reactive context, executes post-reload hooks, and then begins asynchronously watching for file changes. The process continues until interrupted by a keyboard signal.
        """
        call_pre_reload_hooks()
        with suppress(KeyboardInterrupt), HMR_CONTEXT.effect(self.run_entry_file):
            call_post_reload_hooks()
            await self.start_watching()


def cli():
    """
    Runs the command-line interface for the hot module reloading system.
    
    Validates the entry file argument, sets up the import path, initializes the synchronous reloader, replaces the `__main__` module, and starts watching for file changes until interrupted.
    """
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


__version__ = "0.6.2"
