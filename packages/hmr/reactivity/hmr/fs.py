import sys
from collections import defaultdict
from functools import cache
from pathlib import Path

from ..primitives import Subscribable
from ._common import HMR_CONTEXT


@defaultdict
def fs_signals():
    return Subscribable(context=HMR_CONTEXT)


@cache
def setup_fs_audithook():
    @sys.addaudithook
    def _(event: str, args: tuple):
        if event == "open":
            file, _, flags = args

            if (flags % 2 == 0) and HMR_CONTEXT.leaf.current_computations and isinstance(file, str):
                track(file)


def track(file: str | Path):
    fs_signals[Path(file).resolve()].track()


def notify(file: Path):
    fs_signals[file].notify()


__all__ = "notify", "setup_fs_audithook", "track"
