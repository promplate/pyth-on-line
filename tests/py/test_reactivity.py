import gc

from pytest import raises
from utils import capture_stdout

from src.python.common.reactivity import Reactive, State, batch, create_effect, create_memo, create_signal, memoized_method, memoized_property


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

    set_s(2)
    assert s == 2


def test_state_dispose():
    get_s, set_s = create_signal(0)

    results = []

    with create_effect(lambda: results.append(get_s())):
        set_s(1)
        assert results == [0, 1]

    set_s(2)
    assert results == [0, 1]

    with create_effect(results.clear, call_immediately=False):
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

    r.x = 2
    assert r.count == 1
    assert r.size == 0

    r.y = 3
    assert r.size == 6
    assert r.size == 6
    assert r.count == 3


def test_memo_method():
    class Rect:
        x = State(0)
        y = State(0)

        count = 0

        @memoized_method
        def get_size(self):
            self.count += 1
            return self.x * self.y

    r = Rect()

    assert r.get_size() == 0

    r.x = 2
    assert r.count == 1
    assert r.get_size() == 0

    r.y = 3
    assert r.get_size() == 6
    assert r.get_size() == 6
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


def test_nested_batch():
    get_s, set_s = create_signal(0)

    def increment():
        set_s(get_s() + 1)

    with capture_stdout() as stdout, create_effect(lambda: print(get_s())):
        assert stdout == "0\n"
        with batch():
            increment()
            assert stdout == "0\n"
            with batch():
                increment()
                increment()
            assert stdout == "0\n3\n"
            increment()
            increment()
            assert stdout == "0\n3\n"
        assert stdout == "0\n3\n5\n"


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


def test_error_handling():
    get_s, set_s = create_signal(0)

    with raises(ValueError, match="0"):

        @create_effect
        def _():
            raise ValueError(get_s())

    with raises(ValueError, match="1"):
        set_s(1)

    from src.python.common.reactivity.primitives import _current_computations

    assert _current_computations == []


def test_exec_inside_reactive_namespace():
    context = Reactive()

    with raises(NameError):

        @create_effect
        def _():
            exec("print(a)", None, context)

    with capture_stdout() as stdout:
        context["a"] = 123
        assert stdout == "123\n"

    with raises(NameError):
        del context["a"]

    with capture_stdout():
        context["a"] = 234

    with raises(NameError):
        exec("del a", None, context)

    with raises(KeyError):
        del context["a"]

    with capture_stdout() as stdout:
        exec("a = 345", None, context)
        assert context["a"] == 345
        assert stdout == "345\n"


def test_equality_checks():
    get_s, set_s = create_signal(0)
    with capture_stdout() as stdout, create_effect(lambda: print(get_s())):
        assert stdout == "0\n"
        set_s(0)
        assert stdout == "0\n"

    get_s, set_s = create_signal(0, False)
    with capture_stdout() as stdout, create_effect(lambda: print(get_s())):
        assert stdout == "0\n"
        set_s(0)
        assert stdout == "0\n0\n"

    context = Reactive()
    with capture_stdout() as stdout, create_effect(lambda: print(context.get(0))):
        context[0] = None
        assert stdout == "None\nNone\n"
        context[0] = None
        assert stdout == "None\nNone\n"

    context = Reactive(check_equality=False)
    with capture_stdout() as stdout, create_effect(lambda: print(context.get(0))):
        context[0] = None
        assert stdout == "None\nNone\n"
        context[0] = None
        assert stdout == "None\nNone\nNone\n"


def test_reactive_initial_value():
    context = Reactive({1: 2})
    assert context[1] == 2

    with capture_stdout() as stdout, create_effect(lambda: print(context[1])):
        context[1] = 3
        assert stdout == "2\n3\n"


def test_fine_grained_reactivity():
    context = Reactive({1: 2})

    logs_1 = []
    logs_2 = []

    @create_effect
    def _():
        logs_1.append({**context})

    @create_effect
    def _():
        logs_2.append(context[1])

    context[1] = context[2] = 3

    assert logs_1 == [{1: 2}, {1: 3}, {1: 3, 2: 3}]
    assert logs_2 == [2, 3]


def test_get_without_tracking():
    get_s, set_s = create_signal(0)

    with capture_stdout() as stdout, create_effect(lambda: print(get_s(track=False))):
        set_s(1)
        assert get_s() == 1
        assert stdout == "0\n"


def test_state_descriptor_no_leak():
    class Counter:
        value = State(0)

    a = Counter()
    b = Counter()

    a.value = 1

    assert b.value == 0


def test_memo_property_no_leak():
    class Rect:
        x = State(0)
        y = State(0)

        count = 0

        @memoized_property
        def size(self):
            self.count += 1
            return self.x * self.y

    r1 = Rect()
    r2 = Rect()

    r1.x = 2
    r1.y = 3

    assert r1.size == 6
    assert r2.size == 0
