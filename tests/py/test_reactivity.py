import gc
from functools import cache
from inspect import ismethod
from pathlib import Path
from typing import assert_type
from warnings import filterwarnings
from weakref import finalize

from pytest import WarningsRecorder, raises, warns
from reactivity import Reactive, batch, create_signal, effect, memoized, memoized_method, memoized_property
from reactivity.context import default_context, new_context
from reactivity.helpers import DerivedProperty, MemoizedMethod, MemoizedProperty
from reactivity.hmr.proxy import Proxy
from reactivity.primitives import Derived, Effect, Signal, State
from utils import capture_stdout, current_lineno


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

    @effect
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

    with effect(lambda: results.append(get_s())):
        set_s(1)
        assert results == [0, 1]

    set_s(2)
    assert results == [0, 1]

    with effect(results.clear, call_immediately=False):
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

    with effect(lambda: results.append(obj.s)):
        assert results == [0]
        obj.s = 1
        assert results == [0, 1]

    results = []

    with warns(RuntimeWarning) as record, effect(lambda: results.append(obj.v)):
        assert record[0].lineno == current_lineno() - 1
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

    with effect(lambda: results.append(B.s1.get())):
        assert results == [0]
        B.s1.set(1)
        assert results == [0, 1]

    results = []

    with effect(lambda: results.append(B.s2.get())):
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

    @memoized
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

    assert hasattr(r, "size")
    assert hasattr(r, "get_area")


def test_nested_memo(recwarn: WarningsRecorder):
    @memoized
    def f():
        print("f")

    @memoized
    def g():
        f()
        print("g")

    @memoized
    def h():
        g()
        print("h")

    with capture_stdout() as stdout:
        h()
        assert recwarn.pop(RuntimeWarning).lineno == g.fn.__code__.co_firstlineno + 2  # f()
        assert stdout == "f\ng\nh\n"

    with capture_stdout() as stdout:
        g.invalidate()
        assert stdout == ""
        h()
        assert stdout == "g\nh\n"

    filterwarnings("always")  # this is needed to re-enable the warning after it was caught above

    with capture_stdout() as stdout:
        f.invalidate()
        assert recwarn.list == []
        g()
        assert recwarn.pop(RuntimeWarning).lineno == g.fn.__code__.co_firstlineno + 2  # f()
        assert stdout == "f\ng\n"
        h()
        assert stdout == "f\ng\nh\n"
        assert recwarn.list == []


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

    with capture_stdout() as stdout, effect(lambda: print(h())):
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

    @effect
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

    with capture_stdout() as stdout, effect(lambda: print(get_s())):
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

    @effect
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

    with effect(lambda: [*obj]):
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


def test_reactive_lazy_track():
    obj = Reactive()

    with capture_stdout() as stdout:
        with effect(lambda: [*obj, print(123)]):
            obj[1] = 2
            assert stdout.delta == "123\n123\n"
        with effect(lambda: [*obj.keys(), print(123)]):
            obj[2] = 3
            assert stdout.delta == "123\n123\n"
        with effect(lambda: [*obj.values(), print(123)]):
            obj[3] = 4
            assert stdout.delta == "123\n123\n"
        with effect(lambda: [*obj.items(), print(123)]):
            obj[4] = 5
            assert stdout.delta == "123\n123\n"

        # views don't track iteration until actually consumed (e.g., by next() or unpacking)
        with warns(RuntimeWarning) as record, effect(lambda: [obj.keys(), obj.values(), obj.items(), print(123)]):
            assert record[0].lineno == current_lineno() - 1  # because the above line only creates the views but doesn't iterate them
            obj[5] = 6
            assert stdout.delta == "123\n"


def test_reactive_lazy_notify():
    obj = Reactive({1: 2})

    with capture_stdout() as stdout, effect(lambda: print(obj)):
        assert stdout.delta == f"{ {1: 2} }\n"
        obj[1] = 2
        assert stdout.delta == ""
        obj[1] = 3
        assert stdout.delta == f"{ {1: 3} }\n"


def test_fine_grained_reactive():
    obj = Reactive({1: 2, 3: 4})

    a, b, c = [], [], []

    with effect(lambda: a.append(obj[1])), effect(lambda: b.append(list(obj))), effect(lambda: c.append(str(obj))):
        obj[1] = 20

    assert a == [2, 20]
    assert b == [[1, 3]]
    assert c == [str({1: 2, 3: 4}), str({1: 20, 3: 4})]


def test_error_handling():
    get_s, set_s = create_signal(0)

    @memoized
    def should_raise():
        raise ValueError(get_s())

    set_s(2)

    with raises(ValueError, match="2"):
        should_raise()

    set_s(0)

    with raises(ValueError, match="0"):

        @effect
        def _():
            raise ValueError(get_s())

    with raises(ValueError, match="1"):
        set_s(1)

    assert default_context.current_computations == []


def test_context_enter_dependency_restore():
    s = Signal(0)
    always = Signal(0)

    condition = True

    def f():
        always.get()
        if condition:
            print(s.get())
        else:
            raise RuntimeError

    with capture_stdout() as stdout, effect(f):
        assert stdout.delta == "0\n"
        s.set(1)
        assert stdout.delta == "1\n"
        condition = False
        with raises(RuntimeError):
            f()
        with raises(RuntimeError):
            s.set(2)
        condition = True
        assert stdout.delta == ""
        s.set(3)
        assert stdout.delta == "3\n"


def test_exec_inside_reactive_namespace():
    context = Reactive()

    with raises(NameError):

        @effect
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

        with effect(lambda: run("a = 1; b = a + 1; print(b)")):
            assert stdout.delta == "2\n"
            namespace["a"] = 2
            assert stdout.delta == "2\n"

        with effect(lambda: run("print(b)")):
            assert stdout.delta == "2\n"
            namespace["a"] = 3
            assert stdout.delta == ""


def test_equality_checks():
    get_s, set_s = create_signal(0)
    with capture_stdout() as stdout, effect(lambda: print(get_s())):
        assert stdout == "0\n"
        set_s(0)
        assert stdout == "0\n"

    get_s, set_s = create_signal(0, False)
    with capture_stdout() as stdout, effect(lambda: print(get_s())):
        assert stdout == "0\n"
        set_s(0)
        assert stdout == "0\n0\n"

    context = Reactive()
    with capture_stdout() as stdout, effect(lambda: print(context.get(0))):
        context[0] = None
        assert stdout == "None\nNone\n"
        context[0] = None
        assert stdout == "None\nNone\n"

    context = Reactive(check_equality=False)
    with capture_stdout() as stdout, effect(lambda: print(context.get(0))):
        context[0] = None
        assert stdout == "None\nNone\n"
        context[0] = None
        assert stdout == "None\nNone\nNone\n"


def test_reactive_initial_value():
    context = Reactive({1: 2})
    assert context[1] == 2

    with capture_stdout() as stdout, effect(lambda: print(context[1])):
        context[1] = 3
        assert stdout == "2\n3\n"


def test_fine_grained_reactivity():
    context = Reactive({1: 2})

    logs_1 = []
    logs_2 = []

    @effect
    def _():
        logs_1.append({**context})

    @effect
    def _():
        logs_2.append(context[1])

    context[1] = context[2] = 3

    assert logs_1 == [{1: 2}, {1: 3}, {1: 3, 2: 3}]
    assert logs_2 == [2, 3]


def test_reactive_inside_batch():
    context = Reactive()
    logs = []

    @effect
    def _():
        logs.append({**context})

    with batch():
        context[1] = 2
        context[3] = 4
        assert logs == [{}]
    assert logs == [{}, {1: 2, 3: 4}]


def test_get_without_tracking():
    get_s, set_s = create_signal(0)

    with capture_stdout() as stdout, warns(RuntimeWarning) as record, effect(lambda: print(get_s(track=False))):
        assert record[0].lineno == current_lineno() - 1
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

    @memoized
    def f():
        return get_s() * 2

    @memoized
    def g():
        return get_s() * 3

    with capture_stdout() as stdout, effect(lambda: print(f() + g())):
        assert stdout == "0\n"
        set_s(1)
        assert f() + g() == 2 + 3
        assert stdout == "0\n5\n"


def test_memo_as_hard_puller():
    get_s, set_s = create_signal(0)

    @Derived
    def f():
        return get_s() + 1

    @memoized
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

    with capture_stdout() as stdout, effect(lambda: print(f())):
        assert stdout == "[0]\n"
        set_s(1)
        assert stdout == "[0]\n[1]\n"
        set_s(2)
        assert stdout == "[0]\n[1]\n[2]\n"


def test_equality_check_among_arrays():
    import numpy as np

    get_arr, set_arr = create_signal(np.array([[[0, 1]]]))

    with capture_stdout() as stdout, effect(lambda: print(get_arr())):
        assert stdout.delta == "[[[0 1]]]\n"
        set_arr(np.array([[[0, 1]]]))
        assert stdout.delta == ""
        set_arr(np.array([[[1, 2, 3]]]))
        assert stdout.delta == "[[[1 2 3]]]\n"


def test_equality_check_among_dataframes():
    import pandas as pd

    get_df, set_df = create_signal(pd.DataFrame({"a": [0], "b": [1]}))
    with capture_stdout() as stdout, effect(lambda: print(get_df())):
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

        @effect(context=c)
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
    with capture_stdout() as stdout, warns(RuntimeWarning) as record, effect(lambda: exec("""class _: print(a)""", context.raw, context)):
        assert record[0].lineno == current_lineno() - 1  # because of the issue mentioned below
        assert stdout.delta == "123\n"
        context["a"] = 234

        with raises(AssertionError):  # Because of https://github.com/python/cpython/issues/121306
            assert stdout.delta == "234\n", "(xfail)"


def test_unhashable_class():
    class Unhashable:
        x = State(0)

        @DerivedProperty
        def y(self):
            return self.x + 1

        def __eq__(self, value):  # setting __eq__ disables the default __hash__
            return self is value

    u = Unhashable()

    with raises(TypeError):
        hash(u)

    assert u.y == 1
    u.x = 2
    assert u.y == 3

    with raises(NotImplementedError, match="Unhashable\\.y is read-only"):
        del u.y
    with raises(NotImplementedError, match="Unhashable\\.y is read-only"):
        u.y = 5

    # ensure no memory leak

    d = u.__dict__["y"]
    assert isinstance(d, Derived)

    finalize(u, print, "collected")

    del u, d

    with capture_stdout() as stdout:
        gc.collect()
    assert stdout == "collected\n"


def test_descriptors_with_slots():
    class A:
        __slots__ = ()

    class B: ...

    with raises(TypeError) as e1:

        class C(A, B):
            x = State()

    assert "C(A, B)" in e1.exconly()

    with raises(TypeError) as e2:
        exec("class C(A, B):\n    x = State()")

    assert "C(A, B)" in e2.exconly(), e2.exconly()

    class D(A, B):
        x = State(1)

        @DerivedProperty
        def y(self):
            return self.x + 1

        __slots__ = DerivedProperty.SLOT_KEY

    d = D()
    assert d.y == 2

    finalize(d, print, "collected")

    del d

    with capture_stdout() as stdout:
        gc.collect()
    assert stdout == "collected\n"


def test_no_longer_reactive_warning():
    s = Signal(0)

    @cache
    def f():
        return s.get()

    with capture_stdout() as stdout:

        @effect
        def g():
            print(f())

        assert stdout.delta == "0\n"
        assert s.subscribers == {g}

        with warns(RuntimeWarning) as record:
            s.set(1)

    assert stdout.delta == "0\n"
    [warning] = record.list
    assert Path(warning.filename) == Path(__file__)
    assert not g.dependencies


def test_update_vs_set_get_tracking():
    s = Signal(0)

    with warns(RuntimeWarning) as record, Effect(lambda: s.update(lambda x: x + 1)) as e:
        assert record[0].lineno == current_lineno() - 1
        assert s.get() == 1
        assert e not in s.subscribers  # update doesn't track

    # without `.update()`, effects will invalidate themselves, which is unintended mostly
    with Effect(lambda: s.set(s.get() + 1)) as e:
        assert s.get() == 3
        assert e in s.subscribers
        s.set(4)
        assert s.get() == 5  # effect triggered only once because `Batch.flush` has deduplication logic
