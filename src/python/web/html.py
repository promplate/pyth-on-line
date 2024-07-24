from js import Element

from .dom import temp_element


def select(html: str, selector: str):
    with temp_element() as div:
        div.innerHTML = html
        node_list: list[Element] = div.querySelectorAll(selector)  # type: ignore
        return [node.innerHTML for node in node_list]
