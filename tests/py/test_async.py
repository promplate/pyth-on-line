from asyncio import TaskGroup, gather, sleep, timeout
from functools import wraps

from pytest import raises
from reactivity import async_derived
from reactivity.async_primitives import AsyncDerived, AsyncEffect
from reactivity.primitives import Derived, Signal
from utils import Clock, capture_stdout, create_trio_task_factory, run_trio_in_asyncio


def trio(func):
    @wraps(func)
    async def wrapper():
        try:
            return await run_trio_in_asyncio(func)
        except ExceptionGroup as e:
            if len(e.exceptions) == 1:
                raise e.exceptions[0] from None

    return wrapper


async def test_async_effect():
    s = Signal(1)

    async def f():
        print(s.get())

    with capture_stdout() as stdout:
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

        s.set(3)

        async with TaskGroup() as tg:
            with AsyncEffect(f, task_factory=lambda f: tg.create_task(f())) as effect:
                while stdout.delta != "3\n":  # wait for call_immediately to be processed
                    await sleep(0)  # usually calling sleep(0) twice is enough
                s.set(4)
            assert stdout.delta == ""

        assert stdout.delta == "4\n"

        # re-tracked after dispose()

        with raises(RuntimeError, match="TaskGroup <TaskGroup entered> is finished"):
            s.set(5)
        s.set(5)  # no notify()
        with raises(RuntimeError, match="TaskGroup <TaskGroup entered> is finished"):
            s.set(6)


async def test_async_derived():
    s = Signal(0)

    @AsyncDerived
    async def f():
        print(s.get())
        return s.get() + 1

    with capture_stdout() as stdout:
        assert await f() == 1
        assert stdout.delta == "0\n"
        await f()
        assert stdout.delta == ""
        assert not f.dirty
        s.set(1)
        assert stdout.delta == ""
        assert f.dirty
        assert await f() == 2
        assert stdout.delta == "1\n"

    assert {*f.dependencies} == {s}

    @AsyncDerived
    async def g():
        print(await f() + 1)
        return await f() + 1

    with capture_stdout() as stdout:
        assert await g() == 3
        assert stdout.delta == "3\n"
        f.invalidate()
        assert stdout.delta == ""
        assert await g() == 3
        assert stdout.delta == "1\n"  # only f() recomputed

    assert {*g.dependencies} == {f}


async def test_nested_derived():
    s = Signal(0)

    @AsyncDerived
    async def f():
        print("f")
        return s.get()

    @AsyncDerived
    async def g():
        print("g")
        return await f() // 2

    @AsyncDerived
    async def h():
        print("h")
        return await g() // 2

    with capture_stdout() as stdout:
        assert await h() == 0
        assert stdout == "h\ng\nf\n"

    assert {*f.dependencies} == {s}
    assert {*g.dependencies} == {f}
    assert {*h.dependencies} == {g}

    with capture_stdout() as stdout:
        s.set(1)
        assert await f() == 1
        assert stdout.delta == "f\n"
        assert await g() == 0
        assert stdout.delta == "g\n"

    with capture_stdout() as stdout:
        s.set(2)
        assert await h() == 0
        assert stdout.delta == "f\ng\nh\n"


@trio
async def test_trio_nested_derived():
    from trio import open_nursery
    from trio.testing import wait_all_tasks_blocked

    async with open_nursery() as nursery:
        factory = create_trio_task_factory(nursery)

        s = Signal(0)

        @async_derived(task_factory=factory)  # a mixture
        async def f():
            print("f")
            return s.get()

        @async_derived
        async def g():
            print("g")
            return await f() // 2

        @async_derived
        async def h():
            print("h")
            return await g() // 2

        with capture_stdout() as stdout:
            assert await h() == 0
            assert stdout.delta == "h\ng\nf\n"
            s.set(4)
            assert await h() == 1
            assert stdout.delta == "f\ng\nh\n"
            assert h.dirty is False

            with AsyncEffect(h, task_factory=factory) as effect:  # hard puller
                await wait_all_tasks_blocked()
                assert h.subscribers == {effect}

                s.set(5)
                assert stdout.delta == ""
                await wait_all_tasks_blocked()
                assert stdout.delta == "f\ng\n"
                assert [await f(), await g(), await h()] == [5, 2, 1]

                s.set(6)
                assert stdout.delta == ""
                await wait_all_tasks_blocked()
                assert stdout.delta == "f\ng\nh\n"
                assert [await f(), await g(), await h()] == [6, 3, 1]
                assert stdout.delta == ""


async def test_invalidate_before_call_done():
    s = Signal(1)

    @AsyncDerived
    async def f():
        try:
            return s.get()
        finally:
            [await sleep(0) for _ in range(10)]

    call_task = f()

    [await sleep(0) for _ in range(5)]
    # now the first `s.get` is complete
    s.set(2)

    assert await call_task == 1
    assert await f() == 2


async def test_concurrent_tracking():
    a, b, c = Signal(1), Signal(1), Signal(1)

    async with timeout(1), Clock() as clock:

        @clock.async_derived
        async def f():
            await clock.sleep(1)
            return a.get()

        @clock.async_derived
        async def g():
            await clock.sleep(2)
            return b.get()

        @clock.async_derived
        async def h():
            return sum(await gather(f(), g())) + c.get()

        with AsyncEffect(h):
            await clock.fast_forward_to(2)
            assert await h() == 3

            assert {*h.dependencies} == {f, g, c}

            c.set(2)
            assert await h() == 4

            a.set(2)
            await clock.tick()
            assert await h() == 5

            b.set(2)
            await clock.tick()
            assert await f() == 2
            await clock.tick()
            assert await h() == 6


async def test_async_derived_track_behavior():
    """Test that awaiting AsyncDerived doesn't track dependencies, but calling does."""
    s = Signal(1)

    @AsyncDerived
    async def f():
        return s.get()

    @Derived
    @Derived
    def g():
        return f()

    @AsyncDerived
    async def h():
        return await g()

    assert await h() == 1

    assert f.subscribers == {g.fn}  # the inner one
    assert g.subscribers == {h}

    s.set(2)

    assert await h() == 2


@trio
async def test_no_notify_on_first_set():
    from trio import open_nursery
    from trio.testing import wait_all_tasks_blocked

    async with open_nursery() as nursery:
        factory = create_trio_task_factory(nursery)

        s = Signal(0)

        @async_derived(task_factory=factory)
        async def d1():
            return s.get()

        @async_derived(task_factory=factory, check_equality=False)
        async def d2():
            return s.get()

        async def print_values():
            print(await d1(), await d2())

        with capture_stdout() as stdout, AsyncEffect(print_values, task_factory=factory):
            await wait_all_tasks_blocked()
            assert stdout.delta == "0 0\n"
            s.set(1)
            await wait_all_tasks_blocked()
            assert stdout.delta == "1 1\n"
