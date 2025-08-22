from contextlib import contextmanager
from pathlib import Path

from reactivity.hmr.core import SyncReloader
from reactivity.hmr.run import cli
from test_hmr import environment
from utils import capture_stdout


@contextmanager
def mock_reloader():
    SyncReloader.start_watching = lambda self: None  # noqa: ARG005
    try:
        yield
    finally:
        SyncReloader.start_watching = start_watching


start_watching = SyncReloader.start_watching


def test_entry_module():
    with environment() as stdout, mock_reloader():
        Path("a/b").mkdir(parents=True)
        Path("a/b/__main__.py").write_text("if __name__ == '__main__': print(123)")
        assert cli(["-m", "a.b"]) == 0
        assert stdout.delta == "123\n"
        assert cli(["a/b"]) == 0
        assert stdout.delta == "123\n"


def test_entry_file():
    with environment() as stdout, mock_reloader():
        Path("a").mkdir()
        Path("a/b.py").write_text("if __name__ == '__main__': print(123)")
        assert cli(["a/b.py"]) == 0
        assert stdout.delta == "123\n"


def test_help_message():
    with capture_stdout() as stdout:
        assert cli(["--help"]) == 0
        assert "<entry file>" in stdout
        assert "-m <module>" in stdout
    with capture_stdout() as stdout:
        assert cli(["-m"]) == 1
        assert "<entry file>" not in stdout
        assert "-m <module>" in stdout
