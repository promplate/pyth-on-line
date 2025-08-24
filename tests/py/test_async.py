from asyncio import TaskGroup, sleep

from reactivity.async_primitives import AsyncEffect
from reactivity.primitives import Signal
from utils import capture_stdout


async def test_async_effect():
    s = Signal(1)

    async def f():
        print(s.get())

    with capture_stdout() as stdout:
        tg: TaskGroup
        with AsyncEffect(f, False, task_factory=lambda f: tg.create_task(f())) as effect:
            async with TaskGroup() as tg:
                # manually trigger
                await effect()
                assert stdout.delta == "1\n"
                await effect()
                assert stdout.delta == "1\n"

                # automatically trigger
                s.set(2)
                assert stdout.delta == ""
        assert stdout.delta == "2\n"

        del tg
        s.set(3)

        async with TaskGroup() as tg:
            with AsyncEffect(f, task_factory=lambda f: tg.create_task(f())) as effect:
                assert stdout.delta == ""
                await sleep(0.01)
                s.set(4)

        assert stdout.delta == "3\n4\n"
