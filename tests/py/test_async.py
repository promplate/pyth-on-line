import asyncio
from asyncio import TaskGroup, sleep

from pytest import raises
from reactivity.async_primitives import AsyncDerived, AsyncEffect
from reactivity.primitives import Signal
from utils import StepController, TimeEvent, capture_stdout


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


async def test_async_derived_deterministic():
    s = Signal(1)
    step_ctrl = StepController()

    async def compute():
        await step_ctrl.wait_for_step(2)  # wait for step 2 to execute
        return s.get() * 2

    derived = AsyncDerived(compute)

    # Step 1: create derived, won't execute immediately
    assert step_ctrl.current_step == 0

    # Step 2: trigger execution
    await step_ctrl.step()
    result_task = derived()
    await step_ctrl.step()  # advance to step 3, let compute complete

    result = await result_task
    assert result == 2  # 1 * 2
    assert step_ctrl.current_step == 2

    # Step 3: modify signal value, should trigger recomputation
    s.set(3)
    await step_ctrl.step()  # advance to step 4

    # Step 4: get new result
    result_task2 = derived()
    await step_ctrl.step()  # advance to step 5, let compute complete

    result2 = await result_task2
    assert result2 == 6  # 3 * 2
    assert step_ctrl.current_step == 4


async def test_async_derived_with_time_event():
    s = Signal(10)
    event = TimeEvent()
    step_ctrl = StepController()

    async def compute_with_event():
        await step_ctrl.wait_for_step(2)
        await event.wait()  # wait for event to be triggered
        return s.get() + 5

    derived = AsyncDerived(compute_with_event)

    # Step 1: create
    assert step_ctrl.current_step == 0

    # Step 2: start execution, will block at event.wait()
    await step_ctrl.step()
    result_task = derived()
    await step_ctrl.step()  # advance to step 3

    # Task should be waiting for event now
    assert not event.is_set()

    # Step 3: trigger event
    event.set()
    await step_ctrl.step()  # advance to step 4

    # Step 4: get result
    result = await result_task
    assert result == 15  # 10 + 5
    assert step_ctrl.current_step == 3


async def test_async_derived_equality_check():
    s = Signal("hello")
    step_ctrl = StepController()
    computations = []

    async def compute():
        await step_ctrl.wait_for_step(2)
        computations.append(step_ctrl.current_step)
        return s.get()

    derived = AsyncDerived(compute, check_equality=True)

    # Step 1: create
    await step_ctrl.step()

    # Step 2: first computation
    result_task1 = derived()
    await step_ctrl.step()
    result1 = await result_task1
    assert result1 == "hello"
    assert computations == [2]

    # Step 3: same value, should not recompute
    s.set("hello")  # set same value
    await step_ctrl.step()

    result_task2 = derived()
    await step_ctrl.step()
    result2 = await result_task2
    assert result2 == "hello"
    assert computations == [2]  # no new computation

    # Step 4: different value, should recompute
    s.set("world")
    await step_ctrl.step()

    result_task3 = derived()
    await step_ctrl.step()
    result3 = await result_task3
    assert result3 == "world"
    assert computations == [2, 6]  # new computation at step 6


async def test_async_derived_concurrent_independence():
    """Test that concurrent AsyncDerived computations don't interfere with each other"""
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

    # Step 1: create both derived
    assert step_ctrl.current_step == 0

    # Step 2: trigger both computations
    await step_ctrl.step()
    task1 = derived1()
    task2 = derived2()

    # Step 3: advance to let compute1 complete
    await step_ctrl.step()
    result1 = await task1
    assert result1 == 11  # 10 + 1

    # Step 4: advance to let compute2 complete
    await step_ctrl.step()
    result2 = await task2
    assert result2 == 22  # 20 + 2

    # Step 5: modify signals independently
    s1.set(100)
    s2.set(200)
    await step_ctrl.step()

    # Step 6: get new results
    task1_new = derived1()
    task2_new = derived2()
    await step_ctrl.step()  # Step 7

    result1_new = await task1_new
    result2_new = await task2_new

    assert result1_new == 101  # 100 + 1
    assert result2_new == 202  # 200 + 2


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
