import gc
import sys
from collections.abc import Callable
from contextlib import chdir, contextmanager
from tempfile import TemporaryDirectory

from reactivity.hmr.core import ReactiveModule, patch_meta_path
from reactivity.hmr.fs import _filters, fs_signals
from reactivity.hmr.utils import functions, memos

from .fs import FsUtils
from .io import StringIOWrapper, capture_stdout
from .mock import MockReloader


def compose[T1, T2, **P](first: Callable[P, T1], second: Callable[[T1], T2]) -> Callable[P, T2]:
    """to borrow the params from the first function and the return type from the second one"""
    return lambda *args, **kwargs: second(first(*args, **kwargs))


class Environment(FsUtils):
    def __init__(self, stdout: StringIOWrapper):
        self._stdout = stdout

    @property
    def stdout_delta(self):
        return self._stdout.delta

    @property
    def hmr(self):
        def use(reloader: MockReloader):
            """so that using these methods does trigger watchfiles events"""
            self.replace = reloader.replace
            self.write = reloader.write
            return reloader

        return compose(MockReloader, lambda reloader: use(reloader).hmr())

    def __repr__(self):
        return f"Environment(stdout={self._stdout!r})"


@contextmanager
def environment():
    with TemporaryDirectory() as tmpdir, chdir(tmpdir), capture_stdout() as stdout:
        sys.path.append(tmpdir)
        names = {*sys.modules}
        finder = patch_meta_path()
        try:
            yield Environment(stdout)
        finally:
            sys.path.remove(tmpdir)
            for name in {*sys.modules} - names:
                del sys.modules[name]
            finder._unregister()  # noqa: SLF001

            assert _filters == [], _filters

            fs_signals.clear()
            functions.clear()
            memos.clear()
            gc.collect()

            assert len(ReactiveModule.instances) == 0, tuple(ReactiveModule.instances)
