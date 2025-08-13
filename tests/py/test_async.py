from asyncio import TaskGroup, sleep

from reactivity.async_primitives import AsyncEffect
from reactivity.primitives import Signal
from utils import capture_stdout


async def test_async_effect():
    s = Signal(1)

    async def f():
        print(s.get())
        return s.get()

    with capture_stdout() as stdout:
        async with TaskGroup() as tg:
            effect = AsyncEffect(f, False, task_factory=lambda f: tg.create_task(f()))
            await effect()
            assert stdout.delta == "1\n"
            await effect()
            assert stdout.delta == "1\n"
            s.set(2)
            await sleep(0.1)
        assert stdout.delta == "2\n"
