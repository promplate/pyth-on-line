from contextlib import suppress
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from reactivity.hmr.cli import cli
from utils import capture_stdout


def test_entry_module():
    with patch("reactivity.hmr.core.SyncReloader") as mock_reloader:
        mock_reloader.return_value.keep_watching_until_interrupt = lambda: None

        with suppress(SystemExit):
            cli(["-m", "json.tool"])

        mock_reloader.assert_called_once()
        args = mock_reloader.call_args[0]
        assert len(args) == 1
        assert "json" in args[0] and "tool.py" in args[0]


def test_entry_file():
    with NamedTemporaryFile(mode="w", suffix=".py") as f:
        print('print("test")', file=f)

        with patch("reactivity.hmr.core.SyncReloader") as mock_reloader:
            mock_reloader.return_value.keep_watching_until_interrupt = lambda: None

            with suppress(SystemExit):
                cli([f.name])

            mock_reloader.assert_called_once()
            args = mock_reloader.call_args[0]
            assert len(args) == 1
            assert args[0] == f.name


def test_help_message():
    with capture_stdout() as stdout:
        cli(["--help"])
        assert "<entry file>" in stdout
        assert "-m <module>" in stdout
