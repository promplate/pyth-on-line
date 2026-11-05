from asyncio import Event, create_task, sleep, timeout
from weakref import WeakSet

from pytest import mark, raises
from reactivity.async_primitives import AsyncDerived
from reactivity.context import new_context
from reactivity.primitives import Derived, Signal


def order_dependencies(node, *dependencies):
    priority = {dependency: index for index, dependency in enumerate(dependencies)}

    class OrderedDependencies(WeakSet):
        def __iter__(self):
            return iter(sorted(super().__iter__(), key=priority.__getitem__))

    node.dependencies = OrderedDependencies(node.dependencies)


@mark.parametrize("node_type", (Derived, AsyncDerived))
@mark.parametrize("depth", (4, 12))
async def test_shared_dependencies_are_checked_once(node_type, depth, monkeypatch):
    ctx = new_context()
    source = Signal(1, context=ctx)

    async def read_source():
        return source.get()

    nodes = [node_type(read_source if node_type is AsyncDerived else source.get, context=ctx) for _ in range(2)]
    for level in range(depth + 1):

        async def combine_async(deps=tuple(nodes)):
            return await deps[0]() + await deps[1]()

        def combine(deps=tuple(nodes)):
            return deps[0]() + deps[1]()

        nodes = [node_type(combine_async if node_type is AsyncDerived else combine, context=ctx) for _ in range(2 if level < depth else 1)]
    result = nodes[0]

    async def read():
        return await result() if node_type is AsyncDerived else result()

    assert await read() == 2 ** (depth + 1)
    original = node_type._sync_dirty_deps  # noqa: SLF001
    checks = 0

    def sync(*args, **kwargs):
        nonlocal checks
        checks += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(node_type, "_sync_dirty_deps", sync)
    for _ in range(2):
        checks = 0
        assert await read() == 2 ** (depth + 1)
        # Count checks instead of elapsed time so exponential traversal fails reliably.
        assert checks == 1
    for value in (2, 3):
        checks = 0
        source.set(value)
        assert await read() == value * 2 ** (depth + 1)
        assert checks <= 8 * (2 * depth + 3)

    # Another signal must not turn a shared graph back into repeated full traversals.
    unrelated = Signal(0, context=ctx)
    running = True

    async def update_unrelated():
        while running:
            unrelated.update(lambda value: value + 1)
            await sleep(0)

    updater = create_task(update_unrelated())
    try:
        await sleep(0)
        await read()  # settle any notifications from the last value change
        checks = 0
        assert await read() == 3 * 2 ** (depth + 1)
        assert checks == 1
    finally:
        running = False
        await updater


@mark.parametrize("update", ("signal", "invalidate"))
def test_dependency_changes_during_sync(update):
    ctx = new_context()
    source, trigger = Signal(1, context=ctx), Signal(False, context=ctx)
    external = [1]
    upstream = Derived(lambda: source.get() * external[0], context=ctx)
    shared = Derived(upstream, context=ctx)
    left, right = Derived(shared, context=ctx), Derived(shared, context=ctx)

    def write():
        if trigger.get():
            if update == "signal":
                source.set(2)
            else:
                external[0] = 2
                upstream.invalidate()
        return 0

    writer = Derived(write, context=ctx)
    result = Derived(lambda: left() + writer() + right(), context=ctx)
    assert result() == 2
    order_dependencies(result, left, writer, right)
    trigger.set(True)
    assert result() == 4


@mark.parametrize("update", ("signal", "invalidate"))
async def test_dependency_changes_while_sync_is_suspended(update):
    ctx = new_context()
    source, unused = Signal(1, context=ctx), Signal(0, context=ctx)
    external = [1]

    async def read_source():
        return source.get() * external[0]

    ready, resume = Event(), Event()
    suspend = False

    async def read_unused():
        if suspend:
            ready.set()
            await resume.wait()
        return unused.get()

    upstream = ctx.async_derived(read_source)
    shared = ctx.async_derived(upstream)
    left, right = ctx.async_derived(shared), ctx.async_derived(shared)
    middle = ctx.async_derived(read_unused)

    async def read_result():
        return await left() + await middle() + await right()

    result = ctx.async_derived(read_result)
    assert await result() == 2
    order_dependencies(result, left, middle, right)
    # Pause after the shared ancestor is checked, without changing the middle value.
    suspend = True
    middle.invalidate()
    async with timeout(5):
        pending = result()
        await ready.wait()
        if update == "signal":
            source.set(2)
        else:
            external[0] = 2
            upstream.invalidate()
        resume.set()
        assert await pending == 4


@mark.parametrize("node_type", (Derived, AsyncDerived))
async def test_failed_sync_does_not_skip_remaining_dependencies(node_type):
    is_async = node_type is AsyncDerived
    ctx = new_context()
    source = Signal(1, context=ctx)
    fail = False

    def read_left():
        source.get()
        if fail:
            raise ValueError
        return 0

    async def read_left_async():
        return read_left()

    async def read_right_async():
        return source.get()

    left = node_type(read_left_async if is_async else read_left, context=ctx)
    right = node_type(read_right_async, context=ctx) if is_async else node_type(source.get, context=ctx)

    async def combine_async():
        return await left() + await right()

    result = node_type(combine_async if is_async else lambda: left() + right(), context=ctx)

    async def read():
        return await result() if is_async else result()

    assert await read() == 1
    order_dependencies(result, left, right)
    source.set(2)
    fail = True
    with raises(ValueError):
        await read()
    fail = False
    assert await read() == 2
