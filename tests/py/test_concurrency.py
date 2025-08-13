from asyncio import gather, sleep, to_thread
from threading import Barrier

from reactivity.primitives import Batch, Derived, Effect, Signal
from utils import capture_stdout


async def test_threading():
    a = Signal(1)
    b = Signal(2)

    n = 10

    @Derived
    def f():
        x = a.get()
        barrier.wait(timeout=1)
        y = b.get()
        return x * y

    coros = []

    def g():
        # Establish dependency on signals so Effect re-runs when they change,
        # but avoid subscribing to f() to prevent main-thread recomputation
        a.get()
        b.get()

        @coros.append
        @to_thread
        def run():
            v = f()
            print(v)

    async def wait():
        await gather(*coros)
        coros.clear()

    with capture_stdout() as stdout:
        barrier = Barrier(n)
        for _ in range(n):
            Effect(g)
        await wait()
        assert stdout.delta == "2\n" * n

        barrier = Barrier(n)
        a.set(3)
        await sleep(0.1)
        await wait()
        assert stdout.delta == "6\n" * n

        barrier = Barrier(n)
        with Batch():
            a.set(3)
            b.set(2)
        await wait()
        assert stdout.delta == ""
