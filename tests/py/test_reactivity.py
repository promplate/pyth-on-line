import gc

from src.python.common.reactivity import Reactive, State, batch, create_effect, create_memo, create_signal, memoized_property


def test_state_initial_value():
    assert State().get() is None
    assert State(0).get() == 0


def test_state_set():
    s = State(0)
    s.set(1)
    assert s.get() == 1


def test_state_notify():
    get_s, set_s = create_signal(0)

    s = 0

    @create_effect
    def _():
        nonlocal s
        s = get_s()

    set_s(1)
    assert s == 1

    del _
    gc.collect()


def test_state_dispose():
    get_s, set_s = create_signal(0)

    results = []

    with create_effect(lambda: results.append(get_s())):
        set_s(1)
        assert results == [0, 1]

    set_s(2)
    assert results == [0, 1]

    with create_effect(lambda: results.clear(), auto_run=False):
        set_s(3)
        assert results == [0, 1]

    set_s(4)
    assert results == [0, 1]


def test_state_descriptor():
    class Example:
        s = State(0)  # reactive attribute
        v = 0  # normal attribute

    obj = Example()

    results = []

    with create_effect(lambda: results.append(obj.s)):
        assert results == [0]
        obj.s = 1
        assert results == [0, 1]

    results = []

    with create_effect(lambda: results.append(obj.v)):
        assert results == [0]
        obj.v = 1
        assert results == [0]


def test_memo():
    get_s, set_s = create_signal(0)

    count = 0

    @create_memo
    def doubled():
        nonlocal count
        count += 1
        return get_s() * 2

    assert count == 0

    assert doubled() == 0
    assert count == 1

    set_s(1)
    assert count == 1

    assert doubled() == 2
    assert count == 2


def test_memo_property():
    class Rect:
        x = State(0)
        y = State(0)

        count = 0

        @memoized_property
        def size(self):
            self.count += 1
            return self.x * self.y

    r = Rect()

    assert r.size == 0
    assert r.count == 1

    r.x = 2
    assert r.size == 0

    r.y = 3
    assert r.size == 6
    assert r.count == 3


def test_batch():
    class Example:
        value = State(0)

    obj = Example()

    history = []

    @create_effect
    def _():
        history.append(obj.value)

    assert history == [0]

    def increment():
        obj.value += 1

    increment()
    assert history == [0, 1]

    increment()
    increment()
    assert history == [0, 1, 2, 3]

    with batch():
        increment()
        increment()
        assert history == [0, 1, 2, 3]

    assert history == [0, 1, 2, 3, 5]


def test_reactive():
    obj = Reactive()
    obj["x"] = obj["y"] = 0

    size_history = []

    @create_effect
    def _():
        size_history.append(obj["x"] * obj["y"])

    assert size_history == [0]

    obj["x"] = 2
    obj["y"] = 3
    assert size_history == [0, 0, 6]
