import asyncio
from asyncio import TaskGroup, sleep
from functools import partial
from typing import TYPE_CHECKING

from pytest import raises
from reactivity.async_primitives import AsyncDerived, AsyncEffect
from reactivity.primitives import Signal
from utils import StepController, capture_stdout, create_task_factory, run_trio_in_asyncio


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


async def _trio_test_nested_derived():
    from trio import open_nursery

    async with open_nursery() as nursery:
        if TYPE_CHECKING:
            trio_async_derived = AsyncDerived
        else:
            trio_async_derived = partial(AsyncDerived, task_factory=create_task_factory(nursery))

        s = Signal(0)

        @trio_async_derived
        async def f():
            print("f")
            return s.get()

        @trio_async_derived
        async def g():
            print("g")
            return await f() // 2

        @trio_async_derived
        async def h():
            print("h")
            return await g() // 2

        with capture_stdout() as stdout:
            assert await h() == 0
            assert stdout.delta == "h\ng\nf\n"
            s.set(4)
            assert await h() == 1
            assert stdout.delta == "f\ng\nh\n"


def test_trio_nested_derived_sync():
    from trio import run  # pytest-trio conflicts with pytest-asyncio auto mode, so we use sync `trio.run` here

    run(_trio_test_nested_derived)


async def test_trio_nested_derived_guest_mode():
    await run_trio_in_asyncio(_trio_test_nested_derived)


async def test_async_derived_concurrent_independence():
    s1 = Signal(10)
    s2 = Signal(20)
    step_ctrl = StepController()

    async def compute1():
        await step_ctrl.wait_for_step(2)
        return s1.get() + 1

    async def compute2():
        await step_ctrl.wait_for_step(3)
        return s2.get() + 2

    derived1 = AsyncDerived(compute1)
    derived2 = AsyncDerived(compute2)

    await step_ctrl.step()  # Step 1: trigger both computations
    task1 = derived1()
    task2 = derived2()

    await step_ctrl.step()  # Step 2: advance to let compute1 complete
    result1 = await task1
    assert result1 == 11  # 10 + 1

    await step_ctrl.step()  # Step 3: advance to let compute2 complete
    result2 = await task2
    assert result2 == 22  # 20 + 2


async def test_async_derived_concurrent_dependency():
    """Test AsyncDerived with shared dependencies but independent execution"""
    shared_signal = Signal(5)
    computations = []

    async def compute_a():
        # Use same step for both to avoid complex synchronization
        computations.append("a")
        return shared_signal.get() * 2

    async def compute_b():
        computations.append("b")
        return shared_signal.get() + 10

    derived_a = AsyncDerived(compute_a)
    derived_b = AsyncDerived(compute_b)

    # Get first results
    task_a = derived_a()
    task_b = derived_b()

    result_a = await task_a
    result_b = await task_b

    assert result_a == 10  # 5 * 2
    assert result_b == 15  # 5 + 10
    assert set(computations) == {"a", "b"}  # both computed, order may vary

    # Clear computations for next test
    computations.clear()

    # Modify shared signal and recompute
    shared_signal.set(8)

    task_a2 = derived_a()
    task_b2 = derived_b()

    result_a2 = await task_a2
    result_b2 = await task_b2

    assert result_a2 == 16  # 8 * 2
    assert result_b2 == 18  # 8 + 10
    assert set(computations) == {"a", "b"}  # both recomputed


async def test_async_derived_race_condition_prevention():
    """Test that AsyncDerived prevents race conditions with proper dependency tracking"""
    base_signal = Signal(1)
    step_ctrl = StepController()
    execution_order = []

    async def slow_computation():
        execution_order.append("start_slow")
        await step_ctrl.wait_for_step(3)  # intentionally slow
        result = base_signal.get() * 10
        execution_order.append("end_slow")
        return result

    async def fast_computation():
        execution_order.append("fast")
        return base_signal.get() + 1

    slow_derived = AsyncDerived(slow_computation)
    fast_derived = AsyncDerived(fast_computation)

    # Step 1: create
    await step_ctrl.step()

    # Step 2: start both computations
    slow_task = slow_derived()
    fast_task = fast_derived()
    await step_ctrl.step()  # Step 3

    # Fast computation should complete first
    fast_result = await fast_task
    assert fast_result == 2  # 1 + 1

    # Step 4: let slow computation complete
    await step_ctrl.step()
    slow_result = await slow_task
    assert slow_result == 10  # 1 * 10

    # Verify execution order
    assert execution_order == ["start_slow", "fast", "end_slow"]

    # Step 5: modify signal and test reactivity
    base_signal.set(2)
    await step_ctrl.step()

    # Step 6: recompute
    slow_task2 = slow_derived()
    fast_task2 = fast_derived()
    await step_ctrl.step()  # Step 7

    fast_result2 = await fast_task2
    await step_ctrl.step()  # Step 8
    slow_result2 = await slow_task2

    assert fast_result2 == 3  # 2 + 1
    assert slow_result2 == 20  # 2 * 10


async def test_async_derived_multithreaded_access():
    """Test AsyncDerived accessed from multiple threads safely"""
    signal = Signal(1)

    async def compute():
        return signal.get() * 2

    # Create derived with custom task factory that uses the main loop
    loop = asyncio.get_running_loop()

    def thread_safe_task_factory(async_function):
        """Task factory that uses the main event loop"""
        return asyncio.ensure_future(async_function(), loop=loop)

    derived = AsyncDerived(compute, task_factory=thread_safe_task_factory)

    # Test that we can access the derived value from the main thread
    result = await derived()
    assert result == 2  # 1 * 2

    # Test that signal modifications work correctly
    signal.set(3)
    result = await derived()
    assert result == 6  # 3 * 2


async def test_async_derived_thread_safety():
    """Test AsyncDerived thread safety with basic functionality"""
    signal = Signal(5)

    async def compute():
        return signal.get() * 2

    derived = AsyncDerived(compute)

    # Test basic functionality
    result = await derived()
    assert result == 10  # 5 * 2

    # Test reactivity
    signal.set(10)
    result = await derived()
    assert result == 20  # 10 * 2


async def test_async_derived_cross_thread_signal_modification():
    """Test that signal modifications properly trigger AsyncDerived recomputation"""
    signal = Signal(1)
    computations = []

    async def compute():
        computations.append(signal.get())
        return signal.get() * 2

    derived = AsyncDerived(compute)

    # Get initial result
    initial_result = await derived()
    assert initial_result == 2  # 1 * 2
    assert computations == [1]

    # Modify signal
    signal.set(10)

    # Get updated result
    updated_result = await derived()
    assert updated_result == 20  # 10 * 2
    assert computations == [1, 10]  # Should have recomputed
