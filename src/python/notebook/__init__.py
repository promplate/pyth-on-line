import builtins
from ast import parse
from collections.abc import Callable
from contextlib import suppress
from itertools import count

from common.inspection import inspect
from pyodide.ffi import create_once_callable, to_js
from reactivity import create_effect

from .exec import ReactiveNamespace, console_exec_source, exec_source
from .stream import StreamManager


class NotebookAPI:
    def __init__(self):
        """
        Initializes the NotebookAPI with reactive builtins and execution context.

        Creates reactive namespaces for Python builtins and the execution context, and sets up a counter for generating unique input filenames.
        """
        self.builtins = ReactiveNamespace(builtins.__dict__)
        self.context = ReactiveNamespace({"__builtins__": self.builtins, "__name__": "__main__", "__doc__": None, "__package__": None, "__loader__": None, "__spec__": None})
        self.counter = count(1)

    @property
    def filename(self):
        return f"In[{next(self.counter)}]"

    async def run(self, source: str, sync, console=False):
        if console:
            async for value in console_exec_source(self.filename, source, self.context, StreamManager(sync)):
                if value is not None:
                    self.builtins["_"] = value
        else:
            value = await exec_source(self.filename, source, self.context, StreamManager(sync))
            if value is not None:
                self.builtins["_"] = value

    def inspect(self, name: str):
        """
        Inspects the specified variable or object in the current context and builtins.

        Args:
            name: The name of the variable or object to inspect.

        Returns:
            A JavaScript-compatible representation of the inspection result.
        """
        return to_js(inspect(name, self.context, self.builtins))

    def watch(self, name: str, callback: Callable):
        """
        Watches a variable by name and invokes a callback with its inspected value whenever it changes.

        Args:
            name: The name of the variable to watch.
            callback: A function to call with the inspected value each time it updates.

        Returns:
            A callable that, when invoked, stops watching the variable.
        """
        effect = create_effect(lambda: callback(self.inspect(name)))
        return create_once_callable(effect.dispose)

    @staticmethod
    def is_python(source: str):
        """
        Determines whether the given source string is valid Python code.

        Args:
            source: The source code to check.

        Returns:
            True if the source can be parsed as Python code without syntax errors, otherwise False.
        """
        with suppress(SyntaxError):
            parse(source)
            return True
        return False
