from contextlib import contextmanager

from reactivity.hmr.core import SyncReloader
from reactivity.hmr.run import cli
from utils import capture_stdout, environment


@contextmanager
def mock_reloader():
    SyncReloader.start_watching = lambda self: None  # noqa: ARG005
    try:
        yield
    finally:
        SyncReloader.start_watching = start_watching


start_watching = SyncReloader.start_watching


def test_entry_module():
    with environment() as env, mock_reloader():
        env["a/b/__main__.py"] = "if __name__ == '__main__': print(123)"
        assert cli(["-m", "a.b"]) == 0
        assert env.stdout_delta == "123\n"
        assert cli(["a/b"]) == 0
        assert env.stdout_delta == "123\n"


def test_entry_file():
    with environment() as env, mock_reloader():
        env["a/b.py"] = "if __name__ == '__main__': print(123)"
        assert cli(["a/b.py"]) == 0
        assert env.stdout_delta == "123\n"


def test_help_message():
    with capture_stdout() as stdout:
        assert cli(["--help"]) == 0
        assert "<entry file>" in stdout
        assert "-m <module>" in stdout
    with capture_stdout() as stdout:
        assert cli(["-m"]) == 1
        assert "<entry file>" not in stdout
        assert "-m <module>" in stdout
