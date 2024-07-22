from asyncio import ensure_future, gather
from functools import cache

from .fetch import fetch
from .html import select


@cache
def install_requirements():
    from micropip import install

    return ensure_future(install("html2text2"))


async def get_cpython_docs(pathname: str):
    _, html = await gather(install_requirements(), fetch(f"https://docs.python.org/3.12/{pathname}"))
    await install_requirements()

    nodes = select(html, "div.body")
    assert len(nodes) == 1

    from html2text import html2text

    return html2text(nodes[0]).replace("¶", "")
