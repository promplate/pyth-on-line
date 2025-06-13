from collections.abc import MutableMapping
from typing import Any

from ..context import Context
from ..helpers import Reactive


class Proxy[T: MutableMapping](Reactive[str, Any]):
    def __init__(self, initial: T, check_equality=True, *, context: Context | None = None):
        """
        Initializes the Proxy with a mutable mapping and optional configuration.
        
        Args:
        	initial: The mutable mapping to be wrapped and tracked.
        	check_equality: If True, enables equality checks when updating values.
        	context: Optional context object for additional configuration.
        """
        super().__init__(initial, check_equality, context=context)
        self.raw: T = initial

    def __setitem__(self, key, value):
        """
        Sets a key-value pair in the underlying mapping and updates the reactive state.
        
        Updates the wrapped mutable mapping with the given key and value, then propagates
        the change to the reactive layer.
        """
        self.raw[key] = value
        super().__setitem__(key, value)

    def __delitem__(self, key):
        """
        Removes a key and its value from the underlying mapping and updates the reactive state.
        
        Deletes the specified key from the wrapped mutable mapping, then propagates the deletion to the reactive layer.
        """
        del self.raw[key]
        super().__delitem__(key)
