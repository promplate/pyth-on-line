from reactivity import create_effect, create_signal
from reactivity.hmr._experimental import Dirty


def test_dirty_basic():
    call_count = 0

    @Dirty
    def compute():
        nonlocal call_count
        call_count += 1
        return call_count * 2

    assert compute.value is Dirty.UNSET

    assert compute() == 2
    assert call_count == 1
    assert compute.value == 2


def test_dirty_with_dependencies():
    get_s, set_s = create_signal(0)

    call_count = 0

    @Dirty
    def compute():
        nonlocal call_count
        call_count += 1
        return get_s() + 10

    assert compute() == 10
    assert call_count == 1

    assert compute() == 10
    assert call_count == 2

    set_s(5)
    assert compute() == 15
    assert call_count == 4


def test_dirty_notify():
    get_s, set_s = create_signal(0)

    def compute():
        return get_s()

    dirty = Dirty(compute)

    results = []

    @create_effect
    def _():
        results.append(dirty())

    assert results == [0, 0], "(xfail)"  # BUG: dirty() should only be called once

    set_s(1)
    assert results == [0, 0, 1]
