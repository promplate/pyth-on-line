"""Test CLI functionality for -m flag support"""

import sys
import importlib.util
from pathlib import Path
from unittest.mock import patch
import pytest


def test_cli_module_flag_parsing():
    """Test that CLI correctly parses -m flag and resolves modules"""
    
    # Import the cli function to test
    from reactivity.hmr.core import cli
    
    # Test with json module which has a proper file path
    with patch.object(sys, 'argv', ['hmr', '-m', 'json']):
        with patch('reactivity.hmr.core.SyncReloader') as mock_reloader:
            mock_reloader.return_value.keep_watching_until_interrupt = lambda: None
            
            try:
                cli()
                # Should have called SyncReloader with json module path
                mock_reloader.assert_called_once()
                args = mock_reloader.call_args[0]
                assert len(args) == 1
                # json module should have a real file path
                assert args[0] != 'frozen'
                assert 'json' in args[0] and args[0].endswith('.py')
            except SystemExit:
                pass


def test_cli_package_flag_parsing():
    """Test that CLI correctly handles packages with __main__.py"""
    from reactivity.hmr.core import cli
    
    # Create a temporary package structure
    with patch.object(sys, 'argv', ['hmr', '-m', 'json.tool']):
        with patch('reactivity.hmr.core.SyncReloader') as mock_reloader:
            mock_reloader.return_value.keep_watching_until_interrupt = lambda: None
            
            try:
                cli()
                # Should have called SyncReloader with json.tool module path
                mock_reloader.assert_called_once()
                args = mock_reloader.call_args[0]
                assert len(args) == 1
                assert 'json' in args[0] and 'tool.py' in args[0]
            except SystemExit:
                pass


def test_cli_module_not_found():
    """Test that CLI properly handles non-existent modules"""
    from reactivity.hmr.core import cli
    
    with patch.object(sys, 'argv', ['hmr', '-m', 'nonexistent_module_12345']):
        with patch('builtins.print') as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                cli()
            
            assert exc_info.value.code == 1
            # Should have printed error message
            mock_print.assert_called()
            error_msg = str(mock_print.call_args[0][0])
            assert 'Error:' in error_msg
            assert 'nonexistent_module_12345' in error_msg


def test_cli_missing_module_name():
    """Test that CLI handles -m flag without module name"""
    from reactivity.hmr.core import cli
    
    with patch.object(sys, 'argv', ['hmr', '-m']):
        with patch('builtins.print') as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                cli()
            
            assert exc_info.value.code == 1
            # Should have printed usage message
            mock_print.assert_called()
            usage_msg = str(mock_print.call_args[0][0])
            assert 'Usage:' in usage_msg and '-m' in usage_msg


def test_cli_file_mode_still_works():
    """Test that original file-based CLI mode still works"""
    from reactivity.hmr.core import cli
    
    # Create a temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('print("test")')
        temp_file = f.name
    
    try:
        with patch.object(sys, 'argv', ['hmr', temp_file]):
            with patch('reactivity.hmr.core.SyncReloader') as mock_reloader:
                mock_reloader.return_value.keep_watching_until_interrupt = lambda: None
                
                try:
                    cli()
                    # Should have called SyncReloader with file path
                    mock_reloader.assert_called_once()
                    args = mock_reloader.call_args[0]
                    assert len(args) == 1
                    assert args[0] == temp_file
                except SystemExit:
                    pass
    finally:
        Path(temp_file).unlink()


def test_cli_help_message():
    """Test that CLI shows help when no arguments provided"""
    from reactivity.hmr.core import cli
    
    with patch.object(sys, 'argv', ['hmr']):
        with patch('builtins.print') as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                cli()
            
            assert exc_info.value.code == 1
            # Should have printed both usage messages
            assert mock_print.call_count == 2
            calls = [str(call[0][0]) for call in mock_print.call_args_list]
            assert any('<entry file>' in call for call in calls)
            assert any('-m <module>' in call for call in calls)