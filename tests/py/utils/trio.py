from asyncio import get_running_loop
from collections.abc import Awaitable, Callable, Coroutine
from typing import TYPE_CHECKING, Any

from reactivity.async_primitives import AsyncFunction

if TYPE_CHECKING:
    from trio import Nursery


async def run_trio_in_asyncio[T](trio_main: Callable[[], Coroutine[Any, Any, T]]) -> T:
    """
    Run a trio async function inside an asyncio event loop using _guest mode_
    See: https://trio.readthedocs.io/en/stable/reference-lowlevel.html#using-guest-mode-to-run-trio-on-top-of-other-event-loops
    """

    from outcome import Outcome
    from trio.lowlevel import start_guest_run

    loop = get_running_loop()

    future = loop.create_future()

    def done_callback(trio_outcome: Outcome[T]):
        try:
            result = trio_outcome.unwrap()
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)

    start_guest_run(
        trio_main,
        run_sync_soon_not_threadsafe=loop.call_soon,
        run_sync_soon_threadsafe=loop.call_soon_threadsafe,
        done_callback=done_callback,
        host_uses_signal_set_wakeup_fd=True,  # asyncio uses signal.set_wakeup_fd
    )

    return await future


def create_trio_task_factory(nursery: "Nursery"):
    from trio import Event

    def task_factory[T](async_fn: AsyncFunction[T]) -> Awaitable[T]:
        evt = Event()
        res: T
        exc: BaseException | None = None

        @nursery.start_soon
        async def _():
            nonlocal res, exc
            try:
                res = await async_fn()
            except BaseException as e:
                exc = e
            finally:
                evt.set()

        class Future:  # An awaitable that can be awaited multiple times
            def __await__(self):
                yield from evt.wait().__await__()
                if exc is not None:
                    raise exc
                return res  # noqa: F821

        return Future()

    return task_factory
