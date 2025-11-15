"""Performance tests to verify optimizations."""

import numpy as np
import pandas as pd
from reactivity.collections import ReactiveMappingProxy, ReactiveSetProxy
from reactivity.primitives import _equal


def test_equal_with_identity():
    """Test _equal optimizes identity checks."""
    a = [1, 2, 3]
    assert _equal(a, a) is True


def test_equal_with_simple_values():
    """Test _equal works with simple values."""
    assert _equal(1, 1) is True
    assert _equal(1, 2) is False
    assert _equal("hello", "hello") is True
    assert _equal("hello", "world") is False


def test_equal_with_numpy_arrays():
    """Test _equal handles numpy arrays efficiently."""
    a = np.array([1, 2, 3])
    b = np.array([1, 2, 3])
    c = np.array([1, 2, 4])

    assert _equal(a, b) is True
    assert _equal(a, c) is False


def test_equal_with_pandas_dataframes():
    """Test _equal handles pandas DataFrames."""
    df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df3 = pd.DataFrame({"a": [1, 2], "b": [3, 5]})

    assert _equal(df1, df2) is True
    assert _equal(df1, df3) is False


def test_reactive_mapping_len_performance():
    """Test that __len__ uses O(1) operation instead of O(n) sum."""
    # Create a mapping with many items
    data = {f"key_{i}": i for i in range(1000)}
    proxy = ReactiveMappingProxy(data)

    # len() should be fast (O(1)) not slow (O(n))
    assert len(proxy) == 1000

    # Add and remove items
    proxy["new_key"] = 999
    assert len(proxy) == 1001

    del proxy["new_key"]
    assert len(proxy) == 1000


def test_reactive_set_len_performance():
    """Test that __len__ uses O(1) operation instead of O(n) sum."""
    # Create a set with many items
    data = set(range(1000))
    proxy = ReactiveSetProxy(data)

    # len() should be fast (O(1)) not slow (O(n))
    assert len(proxy) == 1000

    # Add and remove items
    proxy.add(1001)
    assert len(proxy) == 1001

    proxy.discard(1001)
    assert len(proxy) == 1000


def test_reactive_mapping_maintains_correctness():
    """Verify that len optimization doesn't break correctness."""
    proxy = ReactiveMappingProxy({})

    assert len(proxy) == 0

    proxy["a"] = 1
    assert len(proxy) == 1

    proxy["b"] = 2
    assert len(proxy) == 2

    del proxy["a"]
    assert len(proxy) == 1

    del proxy["b"]
    assert len(proxy) == 0


def test_reactive_set_maintains_correctness():
    """Verify that len optimization doesn't break correctness."""
    proxy = ReactiveSetProxy(set())

    assert len(proxy) == 0

    proxy.add(1)
    assert len(proxy) == 1

    proxy.add(2)
    assert len(proxy) == 2

    proxy.discard(1)
    assert len(proxy) == 1

    proxy.discard(2)
    assert len(proxy) == 0
