from asyncio import ensure_future
from functools import cache

from .html import select


@cache
def install_requirements():
    from micropip import install

    return ensure_future(install("html2text2"))


async def get_cpython_docs(html: str, pathname: str):
    await install_requirements()

    nodes = select(html, "div.body")
    assert len(nodes) == 1, html

    from html2text import html2text

    base_url = pathname if pathname.endswith(".html") else f"{pathname.rstrip('/')}/"
    return html2text(nodes[0], base_url).replace("¶", "")
