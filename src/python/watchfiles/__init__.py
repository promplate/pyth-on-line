import re
from asyncio import FIRST_COMPLETED, Event, Queue, ensure_future, wait
from collections.abc import AsyncGenerator, Callable, Sequence
from enum import IntEnum
from pathlib import Path
from typing import Literal


class Change(IntEnum):
    added = 1
    modified = 2
    deleted = 3

    def raw_str(self) -> str:
        return self.name


FileChange = tuple[Change, str]

__all__ = "BaseFilter", "Change", "DefaultFilter", "PythonFilter", "awatch"


class BaseFilter:
    __slots__ = "_ignore_dirs", "_ignore_entity_regexes", "_ignore_paths"
    ignore_dirs: Sequence[str] = ()
    ignore_entity_patterns: Sequence[str] = ()
    ignore_paths: Sequence[str | Path] = ()

    def __init__(self) -> None:
        self._ignore_dirs = set(self.ignore_dirs)
        self._ignore_entity_regexes = tuple(re.compile(r) for r in self.ignore_entity_patterns)
        self._ignore_paths = tuple(map(str, self.ignore_paths))

    def __call__(self, change: Change, path: str) -> bool:  # noqa: ARG002
        p = Path(path)
        if any(p in self._ignore_dirs for p in p.parts):
            return False

        entity_name = p.name
        return not (any(r.search(entity_name) for r in self._ignore_entity_regexes) or (self._ignore_paths and path.startswith(self._ignore_paths)))

    def __repr__(self) -> str:
        args = ", ".join(f"{k}={getattr(self, k, None)!r}" for k in self.__slots__)
        return f"{self.__class__.__name__}({args})"


class DefaultFilter(BaseFilter):
    ignore_dirs: Sequence[str] = (
        "__pycache__",
        ".git",
        ".hg",
        ".svn",
        ".tox",
        ".venv",
        ".idea",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        ".hypothesis",
    )

    ignore_entity_patterns: Sequence[str] = (
        r"\.py[cod]$",
        r"\.___jb_...___$",
        r"\.sw.$",
        "~$",
        r"^\.\#",
        r"^\.DS_Store$",
        r"^flycheck_",
    )

    def __init__(
        self,
        *,
        ignore_dirs: Sequence[str] | None = None,
        ignore_entity_patterns: Sequence[str] | None = None,
        ignore_paths: Sequence[str | Path] | None = None,
    ) -> None:
        if ignore_dirs is not None:
            self.ignore_dirs = ignore_dirs
        if ignore_entity_patterns is not None:
            self.ignore_entity_patterns = ignore_entity_patterns
        if ignore_paths is not None:
            self.ignore_paths = ignore_paths

        super().__init__()


class PythonFilter(DefaultFilter):
    def __init__(
        self,
        *,
        ignore_paths: Sequence[str | Path] | None = None,
        extra_extensions: Sequence[str] = (),
    ) -> None:
        self.extensions = (".py", ".pyx", ".pyd", *tuple(extra_extensions))
        super().__init__(ignore_paths=ignore_paths)

    def __call__(self, change: Change, path: str) -> bool:
        return path.endswith(self.extensions) and super().__call__(change, path)


async def awatch(
    *paths: Path | str,
    watch_filter: Callable[[Change, str], bool] | None = DefaultFilter(),
    debounce: int = 1_600,  # noqa: ARG001
    step: int = 50,  # noqa: ARG001
    stop_event: Event | None = None,
    yield_on_timeout: bool = False,  # noqa: ARG001
    raise_interrupt: bool | None = None,  # noqa: ARG001
    force_polling: bool | None = None,  # noqa: ARG001
    recursive: bool = True,  # noqa: ARG001
) -> AsyncGenerator[set[FileChange]]:
    if stop_event is None:
        stop_event = Event()

    watchers.append(watcher := (tuple(Path(p).resolve() for p in paths), queue := Queue()))

    try:
        while True:
            await wait([ensure_future(stop_event.wait()), fut := ensure_future(queue.get())], return_when=FIRST_COMPLETED)
            if stop_event.is_set():
                break
            assert fut.done()
            changes = {fut.result()}
            while not queue.empty():
                changes.add(queue.get_nowait())
            yield {i for i in changes if not watch_filter or watch_filter(*i)}
    finally:
        watchers.remove(watcher)


watchers: list[tuple[tuple[Path, ...], Queue[FileChange]]] = []


def handle_fs_event(change: Literal[1, 2, 3], path: str):
    for paths, queue in watchers:
        event = (Change(change), path)
        event_path = Path(path)
        if any(map(event_path.is_relative_to, paths)):
            queue.put_nowait(event)
