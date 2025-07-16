import sys
from collections import defaultdict
from functools import cache
from pathlib import Path

from ..primitives import Signal


@defaultdict
def fs_signals():
    from .core import HMR_CONTEXT

    return Signal(context=HMR_CONTEXT)


@cache
def setup_fs_audithook():
    @sys.addaudithook
    def _(event: str, args: tuple):
        if event == "open":
            file, mode, _ = args

            if "r" in mode:
                track(file)


def track(file: str | Path):
    fs_signals[Path(file).resolve()].track()


def notify(file: Path):
    fs_signals[file].notify()


__all__ = "notify", "setup_fs_audithook", "track"
