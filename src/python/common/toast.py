from contextlib import contextmanager
from functools import cached_property, partial
from itertools import count
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from ..stub import toast
else:
    from __main__ import toast


class ToastController:
    counter = count()

    @classmethod
    def get_id(cls) -> str:
        return str(next(cls.counter))

    @cached_property
    def id(self):
        return f"toast-{self.get_id()}"

    def loading(self, message: str):
        toast.loading(message, id=self.id, promise=True)

    def dismiss(self):
        toast.dismiss(self.id)

    def __getattr__(self, name: Literal["info", "error", "warning", "success", "message"]):
        assert name in {"info", "error", "warning", "success", "message"}
        func = toast.message if TYPE_CHECKING else getattr(toast, name)
        return partial(func, id=self.id)


@contextmanager
def loading(message: str):
    controller = ToastController()
    controller.loading(message)
    try:
        yield
    except Exception:
        controller.error(message)
        raise
    else:
        controller.success(message)


__all__ = ["loading"]
