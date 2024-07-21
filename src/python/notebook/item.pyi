from typing import Literal, TypedDict

class Item(TypedDict):
    type: Literal["out", "err", "repr"]
    text: str
