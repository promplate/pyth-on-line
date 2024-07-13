from typing import Literal, NotRequired, TypedDict

class Item(TypedDict):
    type: Literal["out", "err", "in", "repr"]
    text: str
    incomplete: NotRequired[bool]
    is_traceback: NotRequired[bool]
