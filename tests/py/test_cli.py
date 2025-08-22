from contextlib import suppress
from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest
from reactivity.hmr.cli import cli


def test_entry_module():
    with patch("reactivity.hmr.cli.SyncReloader") as mock_reloader:
        mock_reloader.return_value.keep_watching_until_interrupt = lambda: None

        with suppress(SystemExit):
            cli(["-m", "json.tool"])

        mock_reloader.assert_called_once()
        args = mock_reloader.call_args[0]
        assert len(args) == 1
        assert "json" in args[0] and "tool.py" in args[0]


def test_entry_file():
    with NamedTemporaryFile(mode="w", suffix=".py") as f:
        f.write('print("test")')
        f.flush()
        temp_file = f.name

        with patch("reactivity.hmr.cli.SyncReloader") as mock_reloader:
            mock_reloader.return_value.keep_watching_until_interrupt = lambda: None

            with suppress(SystemExit):
                cli([temp_file])

            mock_reloader.assert_called_once()
            args = mock_reloader.call_args[0]
            assert len(args) == 1
            assert args[0] == temp_file


def test_help_message():
    with patch("builtins.print") as mock_print:
        with pytest.raises(SystemExit) as exc_info:
            cli([])

        assert exc_info.value.code == 1
        assert mock_print.call_count == 2
        calls = [str(call[0][0]) for call in mock_print.call_args_list]
        assert any("<entry file>" in call for call in calls)
        assert any("-m <module>" in call for call in calls)
