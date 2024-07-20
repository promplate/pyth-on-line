import builtins
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from itertools import count
from traceback import print_exc

from common.inspection import inspect
from pyodide.code import eval_code_async
from pyodide.ffi import to_js


class NotebookAPI:
    def __init__(self):
        self.builtins = builtins.__dict__.copy()
        self.context = {"__builtins__": self.builtins, "__name__": "__main__", "__doc__": None, "__package__": None, "__loader__": None, "__spec__": None}
        self.counter = count(1)

    @property
    def filename(self):
        return f"In[{next(self.counter)}]"

    async def _run(self, source: str):
        value = None
        with redirect_stdout(stdout := StringIO()), redirect_stderr(stderr := StringIO()):
            try:
                value = await eval_code_async(source, self.context, filename=self.filename)
                if value is not None:
                    self.builtins["_"] = value
            except Exception:
                print_exc()

        res = {"out": stdout.getvalue(), "err": stderr.getvalue()}
        if value is not None:
            res["repr"] = repr(value)
        return res

    async def run(self, source):
        return to_js(await self._run(source))

    def inspect(self, name: str):
        return to_js(inspect(name, self.context, self.builtins))
