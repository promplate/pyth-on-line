from functools import partial

from ..context import Context
from ..primitives import Batch


# Global order tracker for consistent cyclic dependency handling
class ModuleOrderTracker:
    def __init__(self):
        self._order_counter = 0
        self.module_order = {}  # Maps ReactiveModule instances to their load order

    def register_module_load(self, module):
        """Register when a module is loaded for the first time to track order."""
        if module not in self.module_order:
            self.module_order[module] = self._order_counter
            self._order_counter += 1

    def get_order(self, module):
        """Get the loading order of a module. Returns float('inf') if not registered."""
        return self.module_order.get(module, float("inf"))

    def clear(self):
        """Clear the order tracker (for testing purposes)."""
        self._order_counter = 0
        self.module_order.clear()


MODULE_ORDER_TRACKER = ModuleOrderTracker()


class OrderedBatch(Batch):
    """A batch that sorts ReactiveModule computations by their initial loading order."""

    def flush(self):
        from inspect import ismethod

        triggered = set()
        while self.callbacks:
            callbacks = self.callbacks - triggered
            self.callbacks.clear()

            # Sort callbacks by module loading order for consistent execution
            def get_module_order(computation):
                # Check if this is a ReactiveModule's load method
                if hasattr(computation, "fn") and ismethod(computation.fn):
                    module = computation.fn.__self__
                    # Check if this is a ReactiveModule instance
                    if hasattr(module, "_ReactiveModule__file"):  # Private attribute access
                        order = MODULE_ORDER_TRACKER.get_order(module)
                        return order
                return float("inf")  # Non-module computations go last

            # Sort callbacks by module order, maintaining deterministic execution
            # Note: We use a stable sort to ensure deterministic behavior
            sorted_callbacks = sorted(callbacks, key=get_module_order)

            for computation in sorted_callbacks:
                if computation in self.callbacks:
                    continue  # skip if re-added during callback
                computation.trigger()
                triggered.add(computation)


class HMRContext(Context):
    """Custom context for HMR with ordered batch processing."""

    @property
    def batch(self):
        return partial(OrderedBatch, context=self)


HMR_CONTEXT = HMRContext([], [])
