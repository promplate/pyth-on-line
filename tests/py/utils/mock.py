from contextlib import contextmanager
from pathlib import Path

from reactivity.hmr.api import LifecycleMixin
from watchfiles import Change

from .fs import FsUtils


class MockReloader(LifecycleMixin, FsUtils):
    started = False

    def event(self, change: Change, filepath: str):
        if self.started:
            self.on_events([(change, filepath)])

    def write(self, filepath: str, content: str):
        existed = Path(filepath).is_file()
        super().write(filepath, content)
        self.event(Change.modified if existed else Change.added, filepath)

    def replace(self, filepath: str, old: str, new: str):
        super().replace(filepath, old, new)
        self.event(Change.modified, filepath)

    @contextmanager
    def hmr(self):
        self.started = True
        try:
            self.run_with_hooks()
            yield self.entry_module
        finally:
            self.clean_up()
            del self.started

    # don't shadow errors

    @property
    def error_filter(self):
        @contextmanager
        def pass_through():
            yield

        return pass_through()

    @error_filter.setter
    def error_filter(self, _): ...
