from asyncio import ensure_future
from functools import cache

from micropip import install


@cache
def install_pure_eval():
    return ensure_future(install("pure-eval"))
