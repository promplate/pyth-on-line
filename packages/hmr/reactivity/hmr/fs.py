import sys
from collections import defaultdict
from collections.abc import Callable
from functools import cache
from pathlib import Path

from ..primitives import Subscribable
from ._common import HMR_CONTEXT


@defaultdict
def fs_signals():
    return Subscribable(context=HMR_CONTEXT)


type PathFilter = Callable[[Path], bool]

_filters: list[PathFilter] = []

add_filter = _filters.append
remove_filter = _filters.remove


@cache
def setup_fs_audithook():
    @sys.addaudithook
    def _(event: str, args: tuple):
        if event == "open":
            file, _, flags = args

            if (flags % 2 == 0) and _filters and isinstance(file, str) and HMR_CONTEXT.leaf.current_computations:
                p = Path(file).resolve()
                if any(f(p) for f in _filters):
                    track(p)


def track(file: Path):
    fs_signals[file].track()


def notify(file: Path):
    fs_signals[file].notify()


__all__ = "notify", "setup_fs_audithook", "track"
