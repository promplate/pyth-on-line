import builtins
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from itertools import count

from common.inspection import inspect
from pyodide.code import eval_code_async
from pyodide.ffi import to_js

from .traceback import get_clean_traceback


class NotebookAPI:
    def __init__(self):
        self.builtins = builtins.__dict__.copy()
        self.context = {"__builtins__": self.builtins, "__name__": "__main__", "__doc__": None, "__package__": None, "__loader__": None, "__spec__": None}
        self.counter = count(1)

    @property
    def filename(self):
        return f"In[{next(self.counter)}]"

    async def _run(self, source: str):
        filename = self.filename
        res = {}
        with redirect_stdout(stdout := StringIO()), redirect_stderr(stderr := StringIO()):
            try:
                value = await eval_code_async(source, self.context, filename=filename)
                if value is not None:
                    self.builtins["_"] = value
                    res["repr"] = repr(value)
            except Exception as e:
                print(get_clean_traceback(e, filename), file=stderr, end="")

        if out := stdout.getvalue():
            res["out"] = out
        if err := stderr.getvalue():
            res["err"] = err

        return res

    async def run(self, source):
        return to_js(await self._run(source))

    def inspect(self, name: str):
        return to_js(inspect(name, self.context, self.builtins))