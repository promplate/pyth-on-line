import builtins
from itertools import count

from common.inspection import inspect
from pyodide.ffi import to_js

from .exec import exec_source
from .stream import StreamManager


class NotebookAPI:
    def __init__(self):
        self.builtins = builtins.__dict__.copy()
        self.context = {"__builtins__": self.builtins, "__name__": "__main__", "__doc__": None, "__package__": None, "__loader__": None, "__spec__": None}
        self.counter = count(1)

    @property
    def filename(self):
        return f"In[{next(self.counter)}]"

    async def run(self, source: str, sync):
        value = await exec_source(self.filename, source, self.context, StreamManager(sync))
        if value is not None:
            self.builtins["_"] = value

    def inspect(self, name: str):
        return to_js(inspect(name, self.context, self.builtins))
