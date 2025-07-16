import sys
from collections import defaultdict
from functools import cache
from os import O_RDONLY, O_RDWR
from pathlib import Path

from ..primitives import Signal
from ._common import HMR_CONTEXT


@defaultdict
def fs_signals():
    return Signal(context=HMR_CONTEXT)


@cache
def setup_fs_audithook():
    READ = O_RDONLY | O_RDWR  # noqa: N806

    current_computations = HMR_CONTEXT.current_computations

    @sys.addaudithook
    def _(event: str, args: tuple):
        if event == "open":
            file, _, flags = args

            if flags & READ and current_computations:
                track(file)


def track(file: str | Path):
    fs_signals[Path(file).resolve()].track()


def notify(file: Path):
    fs_signals[file].notify()


__all__ = "notify", "setup_fs_audithook", "track"
