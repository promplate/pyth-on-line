import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def test_module_flag_parsing():
    from reactivity.hmr.cli import cli

    with patch.object(sys, "argv", ["hmr", "-m", "json"]), patch("reactivity.hmr.cli.SyncReloader") as mock_reloader:
        mock_reloader.return_value.keep_watching_until_interrupt = lambda: None

        try:
            cli()
            mock_reloader.assert_called_once()
            args = mock_reloader.call_args[0]
            assert len(args) == 1
            assert args[0] != "frozen"
            assert "json" in args[0] and args[0].endswith(".py")
        except SystemExit:
            pass


def test_package_flag_parsing():
    from reactivity.hmr.cli import cli

    with patch.object(sys, "argv", ["hmr", "-m", "json.tool"]), patch("reactivity.hmr.cli.SyncReloader") as mock_reloader:
        mock_reloader.return_value.keep_watching_until_interrupt = lambda: None

        try:
            cli()
            mock_reloader.assert_called_once()
            args = mock_reloader.call_args[0]
            assert len(args) == 1
            assert "json" in args[0] and "tool.py" in args[0]
        except SystemExit:
            pass


def test_module_not_found():
    from reactivity.hmr.cli import cli

    with patch.object(sys, "argv", ["hmr", "-m", "nonexistent_module_12345"]), patch("builtins.print") as mock_print:
        with pytest.raises(SystemExit) as exc_info:
            cli()

        assert exc_info.value.code == 1
        mock_print.assert_called()
        error_msg = str(mock_print.call_args[0][0])
        assert "Error:" in error_msg
        assert "nonexistent_module_12345" in error_msg


def test_missing_module_name():
    from reactivity.hmr.cli import cli

    with patch.object(sys, "argv", ["hmr", "-m"]), patch("builtins.print") as mock_print:
        with pytest.raises(SystemExit) as exc_info:
            cli()

        assert exc_info.value.code == 1
        mock_print.assert_called()
        usage_msg = str(mock_print.call_args[0][0])
        assert "Usage:" in usage_msg and "-m" in usage_msg


def test_file_mode():
    from reactivity.hmr.cli import cli

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('print("test")')
        temp_file = f.name

    try:
        with patch.object(sys, "argv", ["hmr", temp_file]), patch("reactivity.hmr.cli.SyncReloader") as mock_reloader:
            mock_reloader.return_value.keep_watching_until_interrupt = lambda: None

            try:
                cli()
                mock_reloader.assert_called_once()
                args = mock_reloader.call_args[0]
                assert len(args) == 1
                assert args[0] == temp_file
            except SystemExit:
                pass
    finally:
        Path(temp_file).unlink()


def test_help_message():
    from reactivity.hmr.cli import cli

    with patch.object(sys, "argv", ["hmr"]), patch("builtins.print") as mock_print:
        with pytest.raises(SystemExit) as exc_info:
            cli()

        assert exc_info.value.code == 1
        assert mock_print.call_count == 2
        calls = [str(call[0][0]) for call in mock_print.call_args_list]
        assert any("<entry file>" in call for call in calls)
        assert any("-m <module>" in call for call in calls)
