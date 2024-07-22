from contextlib import contextmanager
from functools import cache

from js import HTMLDivElement, HTMLTemplateElement, document


@cache
def get_template_node():
    template: HTMLTemplateElement = document.createElement("template")  # type: ignore
    return template.content


@contextmanager
def temp_element():
    root = get_template_node()
    div: HTMLDivElement = root.appendChild(document.createElement("div"))  # type: ignore
    try:
        yield div
    finally:
        div.remove()
