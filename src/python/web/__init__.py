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

    return html2text(nodes[0], f"/cpython/{pathname.removeprefix('/cpython')}").replace("¶", "")
