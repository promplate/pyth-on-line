from inspect import ismethod
from typing import assert_type

import numpy as np
import pandas as pd
from pytest import raises
from reactivity import Reactive, State, batch, create_effect, create_memo, create_signal, memoized_method, memoized_property
from reactivity.context import new_context
from reactivity.helpers import MemoizedMethod, MemoizedProperty
from reactivity.hmr.proxy import Proxy
from reactivity.primitives import Derived, Effect, Signal
from utils import capture_stdout


def test_initial_value():
    assert Signal().get() is None
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


def test_state_class_attribute():
    class A:
        s1 = Signal(0)
        s2 = State(0)

    class B(A): ...

    assert_type(B.s1, Signal[int])
    assert isinstance(B.s2, Signal)

    results = []

    with create_effect(lambda: results.append(B.s1.get())):
        assert results == [0]
        B.s1.set(1)
        assert results == [0, 1]

    results = []

    with create_effect(lambda: results.append(B.s2.get())):
        assert results == [0]
        B.s2.set(1)
        assert results == [0, 1]


def test_gc():
    class E(Effect):
        def __del__(self):
            print("E")

    class S(Signal):
        def __del__(self):
            print("S")

    with capture_stdout() as stdout:
        s = S(0)

        with E(lambda: print(s.get())):  # noqa: F821
            assert stdout.delta == "0\n"
        assert stdout.delta == "E\n"

        E(lambda: print(s.get()))  # noqa: F821
        assert stdout.delta == "0\n"
        del s
        assert stdout.delta == "S\nE\n"


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

    assert ismethod(r.get_size.fn)


def test_memo_class_attribute():
    class Rect:
        x = State(0)
        y = State(0)

        @memoized_property
        def size(self):
            return self.x * self.y

        @memoized_method
        def get_area(self):
            return self.x * self.y

    assert_type(Rect.size, MemoizedProperty[int, Rect])
    assert_type(Rect.get_area, MemoizedMethod[int, Rect])

    assert isinstance(Rect.size, MemoizedProperty)
    assert isinstance(Rect.get_area, MemoizedMethod)

    r = Rect()
    r.x = r.y = 2

    assert r.size == 4
    assert r.get_area() == 4

    assert r in Rect.size.map
    assert r in Rect.get_area.map


def test_nested_memo():
    @create_memo
    def f():
        print("f")

    @create_memo
    def g():
        f()
        print("g")

    @create_memo
    def h():
        g()
        print("h")

    with capture_stdout() as stdout:
        h()
        assert stdout == "f\ng\nh\n"

    with capture_stdout() as stdout:
        g.invalidate()
        assert stdout == ""
        h()
        assert stdout == "g\nh\n"

    with capture_stdout() as stdout:
        f.invalidate()
        g()
        assert stdout == "f\ng\n"
        h()
        assert stdout == "f\ng\nh\n"


def test_derived():
    get_s, set_s = create_signal(0)

    @Derived
    def f():
        print(get_s())
        return get_s() + 1

    with capture_stdout() as stdout:
        assert stdout == ""
        assert f() == 1
        assert stdout == "0\n"
        f()
        assert stdout == "0\n"
        set_s(1)
        assert stdout == "0\n"
        assert f() == 2
        assert stdout == "0\n1\n"
        set_s(1)
        f()
        assert stdout == "0\n1\n"

    @Derived
    def g():
        print(f() + 1)
        return f() + 1

    with capture_stdout() as stdout:
        assert g() == 3
        assert stdout.delta == "3\n"
        f.invalidate()
        assert stdout.delta == ""
        assert g() == 3
        assert stdout.delta == "1\n"  # only f() recomputed


def test_nested_derived():
    get_s, set_s = create_signal(0)

    @Derived
    def f():
        print("f")
        return get_s()

    @Derived
    def g():
        print("g")
        return f() // 2

    @Derived
    def h():
        print("h")
        return g() // 2

    with capture_stdout() as stdout:
        assert h() == 0
        assert stdout == "h\ng\nf\n"

    with capture_stdout() as stdout:
        g.invalidate()
        assert stdout == ""
        assert h() == 0
        assert stdout == "g\n"

    with capture_stdout() as stdout:
        set_s(1)
        assert f() == 1
        assert stdout == "f\n"
        assert g() == 0
        assert stdout == "f\ng\n"

    with capture_stdout() as stdout:
        set_s(2)
        assert stdout == ""
        assert g() == 1
        assert stdout == "f\ng\n"
        assert h() == 0
        assert stdout == "f\ng\nh\n"

    with capture_stdout() as stdout, create_effect(lambda: print(h())):
        assert stdout.delta == "0\n"
        set_s(3)
        assert stdout.delta == "f\ng\n"
        set_s(4)
        assert stdout.delta == "f\ng\nh\n1\n"
        set_s(5)
        assert stdout.delta == "f\ng\n"
        set_s(6)
        assert stdout.delta == "f\ng\nh\n"


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
    obj = Reactive[str, int]()
    obj["x"] = obj["y"] = 0

    size_history = []

    @create_effect
    def _():
        size_history.append(obj["x"] * obj["y"])

    assert size_history == [0]

    obj["x"] = 2
    obj["y"] = 3
    assert size_history == [0, 0, 6]


def test_reactive_spread():
    obj = Reactive()
    with raises(KeyError, match="key"):
        obj["key"]

    assert {**obj} == {}
    assert len(obj) == 0


def test_reactive_tracking():
    obj = Reactive()

    with create_effect(lambda: [*obj]):
        """

        Evaluating `list(obj)` or `[*obj]` will invoke `__iter__` and `__len__` (I don't know why)
        Both methods internally call `track()`
        Inside `track()`, `last.dependencies.add(self)` tries to add the Reactive object to a weak set
        This ends up calling `__eq__`, which in turn calls `items()`, leading to infinite recursion

        """


def test_reactive_repr():
    obj = Reactive()

    with raises(KeyError):
        obj["x"]

    assert repr(obj) == "{}"
    assert not obj.items()


def test_reactive_lazy_notify():
    obj = Reactive({1: 2})

    with capture_stdout() as stdout, create_effect(lambda: print(obj)):
        assert stdout.delta == f"{ {1: 2} }\n"
        obj[1] = 2
        assert stdout.delta == ""
        obj[1] = 3
        assert stdout.delta == f"{ {1: 3} }\n"


def test_fine_grained_reactive():
    obj = Reactive({1: 2, 3: 4})

    a, b, c = [], [], []

    with create_effect(lambda: a.append(obj[1])), create_effect(lambda: b.append(list(obj))), create_effect(lambda: c.append(str(obj))):
        obj[1] = 20

    assert a == [2, 20]
    assert b == [[1, 3]]
    assert c == [str({1: 2, 3: 4}), str({1: 20, 3: 4})]


def test_error_handling():
    get_s, set_s = create_signal(0)

    @create_memo
    def should_raise():
        raise ValueError(get_s())

    set_s(2)

    with raises(ValueError, match="2"):
        should_raise()

    set_s(0)

    with raises(ValueError, match="0"):

        @create_effect
        def _():
            raise ValueError(get_s())

    with raises(ValueError, match="1"):
        set_s(1)

    from reactivity.context import default_context

    assert default_context.current_computations == []


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


def test_complex_exec():
    namespace = type("", (Reactive, dict), {})()

    def run(source: str):
        return exec(source, namespace, namespace)

    with capture_stdout() as stdout:
        run("a = 1; b = a + 1; print(b)")
        assert stdout.delta == "2\n"
        assert {**namespace} == {"a": 1, "b": 2}

        with create_effect(lambda: run("a = 1; b = a + 1; print(b)")):
            assert stdout.delta == "2\n"
            namespace["a"] = 2
            assert stdout.delta == "2\n"

        with create_effect(lambda: run("print(b)")):
            assert stdout.delta == "2\n"
            namespace["a"] = 3
            assert stdout.delta == ""


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


def test_reactive_inside_batch():
    context = Reactive()
    logs = []

    @create_effect
    def _():
        logs.append({**context})

    with batch():
        context[1] = 2
        context[3] = 4
        assert logs == [{}]
    assert logs == [{}, {1: 2, 3: 4}]


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


def test_effect_with_memo():
    get_s, set_s = create_signal(0)

    @create_memo
    def f():
        return get_s() * 2

    @create_memo
    def g():
        return get_s() * 3

    with capture_stdout() as stdout, create_effect(lambda: print(f() + g())):
        assert stdout == "0\n"
        set_s(1)
        assert f() + g() == 2 + 3
        assert stdout == "0\n5\n"


def test_memo_as_hard_puller():
    get_s, set_s = create_signal(0)

    @Derived
    def f():
        return get_s() + 1

    @create_memo
    def g():
        return f() + 1

    assert g() == 2
    set_s(2)
    assert g() == 4


def test_no_notify_on_first_set():
    get_s, set_s = create_signal(0)

    @Derived
    def f():
        return [get_s()]

    with capture_stdout() as stdout, create_effect(lambda: print(f())):
        assert stdout == "[0]\n"
        set_s(1)
        assert stdout == "[0]\n[1]\n"
        set_s(2)
        assert stdout == "[0]\n[1]\n[2]\n"


def test_equality_check_among_arrays():
    get_arr, set_arr = create_signal(np.array([[[0, 1]]]))

    with capture_stdout() as stdout, create_effect(lambda: print(get_arr())):
        assert stdout.delta == "[[[0 1]]]\n"
        set_arr(np.array([[[0, 1]]]))
        assert stdout.delta == ""
        set_arr(np.array([[[1, 2, 3]]]))
        assert stdout.delta == "[[[1 2 3]]]\n"


def test_equality_check_among_dataframes():
    get_df, set_df = create_signal(pd.DataFrame({"a": [0], "b": [1]}))
    with capture_stdout() as stdout, create_effect(lambda: print(get_df())):
        assert stdout.delta == "   a  b\n0  0  1\n"
        set_df(pd.DataFrame({"a": [0], "b": [1]}))
        assert stdout.delta == ""
        set_df(pd.DataFrame({"a": [1], "b": [2]}))
        assert stdout.delta == "   a  b\n0  1  2\n"


def test_context():
    a = new_context()
    b = new_context()

    class Rect:
        x = State(1, context=a)
        y = State(2, context=b)

        @property
        def size(self):
            return self.x * self.y

    r = Rect()

    with capture_stdout() as stdout, a.effect(lambda: print(f"a{r.size}"), context=a), b.effect(lambda: print(f"b{r.size}"), context=b):
        assert stdout.delta == "a2\nb2\n"
        r.x = 3
        assert stdout.delta == "a6\n"
        r.y = 4
        assert stdout.delta == "b12\n"


def test_context_usage_with_reactive_namespace():
    c = new_context()
    dct = Reactive(context=c)

    with capture_stdout() as stdout:

        @c.effect
        def _():
            try:
                print(dct[1])
            except KeyError:
                print()

        assert stdout.delta == "\n"
        dct[1] = 2
        assert stdout.delta == "2\n"


def test_reactive_proxy():
    context = Proxy({"a": 123})
    with capture_stdout() as stdout, create_effect(lambda: exec("""class _: print(a)""", context.raw, context)):
        assert stdout.delta == "123\n"
        context["a"] = 234

        with raises(AssertionError):  # Because of https://github.com/python/cpython/issues/121306
            assert stdout.delta == "234\n", "(xfail)"
