"""Test for issue #273 - Double buffering module namespace"""

import random
from pathlib import Path

import pytest
from utils import environment


def test_mutable_object_reassignment_triggers_reload():
    """Test that reassigning mutable objects triggers HMR even when content is initially the same.
    
    This tests the fix for issue #273 where:
    1. A module assigns a = []
    2. The module mutates a by doing a.append(something)
    3. On reload, a = [] again should trigger notifications even though [] == []
    because the new list will have different content after mutations.
    """
    with environment() as env:
        # Module that exhibits the double buffering issue
        env["target.py"] = """
import random
a = []
a.append(random.random())
print(f"target: {len(a)} items")
"""
        
        # Module that depends on target
        env["main.py"] = """
from target import a
print(f"main: imported {len(a)} items")
"""
        
        with env.hmr("main.py"):
            output1 = env.stdout_delta
            assert "target: 1 items" in output1
            assert "main: imported 1 items" in output1
            
            # Modify target.py - same assignment but different result
            env["target.py"] = """
import random
a = []  # Same assignment - should trigger due to mutable object handling
a.append(random.random())
a.append(random.random())  # Add two items this time
print(f"target: {len(a)} items")
"""
            
            output2 = env.stdout_delta
            # Should have reloaded and shown the new behavior
            assert "target: 2 items" in output2
            assert "main: imported 2 items" in output2


def test_mutable_containers_always_trigger():
    """Test that all mutable container types trigger notifications on reassignment."""
    with environment() as env:
        env["containers.py"] = """
import random

# Different mutable containers
my_list = []
my_dict = {}
my_set = set()

my_list.append(random.random())
my_dict['key'] = random.random()
my_set.add(random.random())

print(f"list:{len(my_list)} dict:{len(my_dict)} set:{len(my_set)}")
"""
        
        env["main.py"] = """
from containers import my_list, my_dict, my_set
print(f"imported - list:{len(my_list)} dict:{len(my_dict)} set:{len(my_set)}")
"""
        
        with env.hmr("main.py"):
            output1 = env.stdout_delta
            assert "list:1 dict:1 set:1" in output1
            
            # Reassign all containers to same "empty" values
            env["containers.py"] = """
import random

# Same assignments but will have different content
my_list = []  # list
my_dict = {}  # dict
my_set = set()  # set

# Add different amounts this time
my_list.extend([random.random(), random.random()])
my_dict.update({'a': random.random(), 'b': random.random()})
my_set.update([random.random(), random.random()])

print(f"list:{len(my_list)} dict:{len(my_dict)} set:{len(my_set)}")
"""
            
            output2 = env.stdout_delta
            # All should have reloaded
            assert "list:2 dict:2 set:2" in output2


def test_immutable_objects_different_values_trigger():
    """Test that immutable objects with different values still trigger (no regression)."""
    with environment() as env:
        env["immutable.py"] = """
a = 42
print(f"a={a}")
"""
        
        env["main.py"] = """
from immutable import a
print(f"imported a={a}")
"""
        
        with env.hmr("main.py"):
            output1 = env.stdout_delta
            assert "a=42" in output1
            assert "imported a=42" in output1
            
            # Change the value - should trigger
            env["immutable.py"] = """
a = 43  # Different value
print(f"a={a}")
"""
            
            output2 = env.stdout_delta
            assert "a=43" in output2
            assert "imported a=43" in output2