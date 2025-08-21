#!/usr/bin/env python3
"""Test script to verify CLI functionality"""

import sys
import importlib.util
from pathlib import Path

def test_cli():
    """Simulate the CLI function to test -m flag logic"""
    
    # Save original argv
    original_argv = sys.argv.copy()
    
    # Test cases
    test_cases = [
        # Test -m with existing module
        ["test_cli.py", "-m", "simple_module"],
        # Test -m with test package
        ["test_cli.py", "-m", "test_package"],
        # Test regular file
        ["test_cli.py", "simple_module.py"],
        # Test help
        ["test_cli.py"],
        # Test -m with non-existent module
        ["test_cli.py", "-m", "nonexistent_module"],
        # Test -m without module name
        ["test_cli.py", "-m"],
        # Test non-existent file
        ["test_cli.py", "nonexistent.py"],
    ]
    
    for i, test_argv in enumerate(test_cases):
        print(f"\n=== Test Case {i+1}: {' '.join(test_argv)} ===")
        sys.argv = test_argv
        
        try:
            # Simulate the CLI logic
            if len(sys.argv) < 2:
                print(" Usage: hmr <entry file>, just like python <entry file>")
                print(" Usage: hmr -m <module>, just like python -m <module>\n")
                continue
            
            sys.argv.pop(0)  # this file itself
            
            # Handle -m flag for module execution
            if sys.argv[0] == "-m":
                if len(sys.argv) < 2:
                    print(" Usage: hmr -m <module>, just like python -m <module>\n")
                    continue
                
                module_name = sys.argv[1]
                sys.argv.pop(0)  # remove -m flag
                
                # Find the module using importlib
                try:
                    spec = importlib.util.find_spec(module_name)
                    if spec is None:
                        raise ModuleNotFoundError(f"No module named '{module_name}'")
                    
                    # Check if it's a package (has submodule_search_locations)
                    if spec.submodule_search_locations:
                        # It's a package, look for __main__.py
                        main_spec = importlib.util.find_spec(f"{module_name}.__main__")
                        if main_spec and main_spec.origin:
                            entry = main_spec.origin
                        else:
                            raise ModuleNotFoundError(f"No module named '{module_name}.__main__'; '{module_name}' is a package and cannot be directly executed")
                    elif spec.origin is None:
                        raise ModuleNotFoundError(f"Cannot find entry point for module '{module_name}'")
                    else:
                        entry = spec.origin
                    
                    print(f"✓ Found module '{module_name}' at: {entry}")
                except ModuleNotFoundError as e:
                    print(f"✗ Error: {e}")
                    continue
            else:
                # Original file-based behavior
                entry = sys.argv[0]
                if not (path := Path(entry)).is_file():
                    print(f"✗ FileNotFoundError: {path.resolve()}")
                    continue
                
                print(f"✓ Found file: {entry}")
            
            path = Path(entry)
            print(f"✓ Entry path: {path}")
            print(f"✓ Parent directory: {path.parent.resolve()}")
            
        except Exception as e:
            print(f"✗ Exception: {e}")
        finally:
            # Restore argv for next test
            sys.argv = original_argv.copy()

if __name__ == "__main__":
    test_cli()