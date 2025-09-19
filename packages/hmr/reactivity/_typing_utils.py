from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import deprecated  # noqa: UP035
else:
    deprecated = lambda _: lambda _: _  # noqa: E731
