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
    """
    Tests that setting a new value on a State updates its stored value correctly.
    """
    s = State(0)
    s.set(1)
    assert s.get() == 1


def test_state_notify():
    """
    Tests that effects created with `create_effect` react to changes in signals.

    Verifies that updating a signal via its setter triggers the associated effect and updates dependent state.
    """
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
    """
    Tests that effects stop reacting to signal changes after disposal and that effects with call_immediately=False do not execute until triggered by a dependency change.
    """
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
    """
    Tests that State descriptors on class attributes are reactive, triggering effects on value changes, while normal attributes do not trigger effects.
    """

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
    """
    Tests that Signal and State used as class attributes are correctly inherited, typed, and remain reactive, ensuring effects respond to updates on subclass attributes.
    """

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
    """
    Tests that Effect and Signal objects print messages upon garbage collection, verifying that cleanup occurs when they are deleted or go out of scope.
    """

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
    """
    Tests memoized computation with create_memo, ensuring lazy evaluation and caching.

    Verifies that the memoized function is only recomputed when its dependencies change, and that repeated calls without changes do not trigger recomputation.
    """
    get_s, set_s = create_signal(0)

    count = 0

    @create_memo
    def doubled():
        """
        Computes and returns twice the current value of `s`, incrementing the `count` variable.

        Increments the external `count` variable each time the function is called, then returns double the value obtained from `get_s()`.
        """
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
    """
    Tests that the `memoized_property` decorator correctly caches computed property values and invalidates the cache when dependent reactive state attributes change.
    """

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
            """
            Calculates the area based on the current values of x and y.

            Increments the internal count each time the method is called.

            Returns:
                The product of x and y.
            """
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
    """
    Tests that memoized properties and methods are correctly typed and stored as class attributes, and that their instance caches are maintained and updated as expected.
    """

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
    """
    Tests nested memoized computations and their invalidation behavior.

    Verifies that nested memoized functions recompute only when their dependencies are invalidated, and that recomputation order is correct. Ensures that invalidating an inner memo triggers selective recomputation of dependent memos.
    """

    @create_memo
    def f():
        print("f")

    @create_memo
    def g():
        """
        Calls the function `f` and prints 'g' to standard output.
        """
        f()
        print("g")

    @create_memo
    def h():
        """
        Calls the function `g` and prints 'h' to standard output.
        """
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
    """
    Tests the behavior of the `Derived` decorator for reactive computed values.

    Verifies that derived computations cache their results, only recompute when dependencies change, and support explicit invalidation. Also checks correct propagation of invalidation in nested derived computations and that side effects (such as print statements) occur only on recomputation.
    """
    get_s, set_s = create_signal(0)

    @Derived
    def f():
        """
        Returns the value of `get_s()` incremented by 1 after printing its current value.
        """
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
        """
        Calls the function `f`, adds 1 to its result, prints the value, and returns it.
        """
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
    """
    Tests nested derived computations for correct invalidation, recomputation order, and effect propagation.

    Verifies that nested `@Derived` functions recompute only when their dependencies change, that invalidation propagates selectively, and that effects depending on derived values are triggered in the correct order. Also checks that redundant invalidations do not cause unnecessary recomputation.
    """
    get_s, set_s = create_signal(0)

    @Derived
    def f():
        """
        Returns the result of get_s() after printing 'f' to standard output.
        """
        print("f")
        return get_s()

    @Derived
    def g():
        """
        Calls function f(), divides its result by 2, and returns the result after printing 'g'.
        """
        print("g")
        return f() // 2

    @Derived
    def h():
        """
        Calls the function `g`, prints 'h', and returns half of its result.
        """
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
    """
    Tests that state updates within a batch are deferred and effects are notified only once after the batch completes.
    """

    class Example:
        value = State(0)

    obj = Example()

    history = []

    @create_effect
    def _():
        history.append(obj.value)

    assert history == [0]

    def increment():
        """
        Increments the value attribute of the obj object by one.
        """
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
    """
    Tests that nested batching defers effect notifications until the outermost batch completes.

    Verifies that multiple state updates within nested `batch()` contexts only trigger effect execution after all batches have exited, ensuring correct notification order and batching semantics.
    """
    get_s, set_s = create_signal(0)

    def increment():
        """
        Increments the value of the signal `s` by one.
        """
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
    """
    Tests that a Reactive dictionary triggers effects when its keys are updated.

    Verifies that effects depending on specific keys are re-executed when those keys change, and that the computed values reflect the latest state.
    """
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
    """
    Tests spreading and length operations on an empty Reactive object.

    Verifies that accessing a missing key raises KeyError, spreading the object yields an empty dictionary, and its length is zero.
    """
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
    """
    Tests the string representation and item iteration of an empty Reactive object.

    Verifies that accessing a missing key raises KeyError, the representation is an empty dictionary, and item iteration yields no items.
    """
    obj = Reactive()

    with raises(KeyError):
        obj["x"]

    assert repr(obj) == "{}"
    assert not obj.items()


def test_reactive_lazy_notify():
    """
    Tests that a Reactive object only notifies effects when a value actually changes.

    Verifies that setting a key to its current value does not trigger effect notifications, while changing the value does.
    """
    obj = Reactive({1: 2})

    with capture_stdout() as stdout, create_effect(lambda: print(obj)):
        assert stdout.delta == f"{ {1: 2} }\n"
        obj[1] = 2
        assert stdout.delta == ""
        obj[1] = 3
        assert stdout.delta == f"{ {1: 3} }\n"


def test_fine_grained_reactive():
    """
    Tests fine-grained reactivity of the Reactive object for key access and full object views.

    Verifies that effects depending on individual keys, the list of keys, and the string representation of a Reactive object are notified appropriately when only a specific key is updated.
    """
    obj = Reactive({1: 2, 3: 4})

    a, b, c = [], [], []

    with create_effect(lambda: a.append(obj[1])), create_effect(lambda: b.append(list(obj))), create_effect(lambda: c.append(str(obj))):
        obj[1] = 20

    assert a == [2, 20]
    assert b == [[1, 3]]
    assert c == [str({1: 2, 3: 4}), str({1: 20, 3: 4})]


def test_error_handling():
    """
    Tests that exceptions raised inside memoized computations and effects propagate correctly and that the reactive context is properly cleaned up after errors.
    """
    get_s, set_s = create_signal(0)

    @create_memo
    def should_raise():
        """
        Raises a ValueError with a message obtained from get_s().
        """
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
    """
    Tests executing code with `exec` inside a `Reactive` namespace.

    Verifies that variable access, assignment, and deletion within a `Reactive` context behave as expected, including correct exception handling and effect triggering on updates.
    """
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
    """
    Tests executing complex code snippets with exec in a Reactive subclass namespace.

    Verifies that variable assignments, updates, and effect-triggered re-execution work as expected within a reactive dictionary context, including correct propagation of changes and output capture.
    """
    namespace = type("", (Reactive, dict), {})()

    def run(source: str):
        """
        Executes the given source code string within the provided namespace.

        Args:
            source: The Python source code to execute.
        """
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
    """
    Tests equality check behavior for signals and reactive dictionaries.

    Verifies that signals and reactive dictionaries with equality checking enabled do not trigger redundant notifications when set to the same value, while disabling equality checks causes notifications on every set, even if the value does not change.
    """
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
    """
    Tests that a Reactive object initialized with a dictionary returns the correct initial value and triggers effects when updated.
    """
    context = Reactive({1: 2})
    assert context[1] == 2

    with capture_stdout() as stdout, create_effect(lambda: print(context[1])):
        context[1] = 3
        assert stdout == "2\n3\n"


def test_fine_grained_reactivity():
    """
    Tests that effects react selectively to changes in a Reactive dictionary.

    Verifies that an effect tracking the full dictionary is notified on any key change, while an effect tracking a specific key is only notified when that key changes.
    """
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
    """
    Tests that multiple updates to a Reactive dictionary within a batch trigger a single effect notification after the batch completes.

    Ensures that the effect observes the combined state changes only once, after all batched updates are applied.
    """
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
    """
    Tests that a signal's value can be accessed without tracking dependencies inside an effect.

    Verifies that using `get_s(track=False)` inside an effect does not establish a reactive dependency, so subsequent updates do not trigger the effect.
    """
    get_s, set_s = create_signal(0)

    with capture_stdout() as stdout, create_effect(lambda: print(get_s(track=False))):
        set_s(1)
        assert get_s() == 1
        assert stdout == "0\n"


def test_state_descriptor_no_leak():
    """
    Tests that State descriptors do not share state between different instances of a class.

    Ensures that assigning a value to a State attribute on one instance does not affect the value on another instance.
    """

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
            """
            Calculates the product of x and y, incrementing the count each time it is called.

            Returns:
                The product of self.x and self.y.
            """
            self.count += 1
            return self.x * self.y

    r1 = Rect()
    r2 = Rect()

    r1.x = 2
    r1.y = 3

    assert r1.size == 6
    assert r2.size == 0


def test_effect_with_memo():
    """
    Tests that multiple memoized computations can be used within a single effect and that the effect reacts correctly to their updates.

    Verifies that the effect prints the sum of two memoized values, and that updates to the underlying signal trigger recomputation and effect execution as expected.
    """
    get_s, set_s = create_signal(0)

    @create_memo
    def f():
        """
        Returns twice the value obtained from get_s().
        """
        return get_s() * 2

    @create_memo
    def g():
        """
        Returns three times the current value of the signal obtained from get_s().
        """
        return get_s() * 3

    with capture_stdout() as stdout, create_effect(lambda: print(f() + g())):
        assert stdout == "0\n"
        set_s(1)
        assert f() + g() == 2 + 3
        assert stdout == "0\n5\n"


def test_memo_as_hard_puller():
    """
    Tests that a memoized computation can depend on a derived computation and updates correctly when dependencies change.
    """
    get_s, set_s = create_signal(0)

    @Derived
    def f():
        """
        Returns the value of `get_s()` incremented by 1.
        """
        return get_s() + 1

    @create_memo
    def g():
        """
        Returns the result of calling function f() incremented by 1.
        """
        return f() + 1

    assert g() == 2
    set_s(2)
    assert g() == 4


def test_no_notify_on_first_set():
    """
    Tests that effects are not notified on the initial set if the value does not change.

    Verifies that an effect only reacts to subsequent changes in a signal's value, and not when the initial set matches the default value.
    """
    get_s, set_s = create_signal(0)

    @Derived
    def f():
        """
        Returns a list containing the result of calling get_s().
        """
        return [get_s()]

    with capture_stdout() as stdout, create_effect(lambda: print(f())):
        assert stdout == "[0]\n"
        set_s(1)
        assert stdout == "[0]\n[1]\n"
        set_s(2)
        assert stdout == "[0]\n[1]\n[2]\n"


def test_equality_check_among_arrays():
    """
    Tests that reactive signals holding NumPy arrays only trigger effects when the array content changes.

    Verifies that setting a signal to a new NumPy array with identical content does not notify effects, while changing the array's content does.
    """
    get_arr, set_arr = create_signal(np.array([[[0, 1]]]))

    with capture_stdout() as stdout, create_effect(lambda: print(get_arr())):
        assert stdout.delta == "[[[0 1]]]\n"
        set_arr(np.array([[[0, 1]]]))
        assert stdout.delta == ""
        set_arr(np.array([[[1, 2, 3]]]))
        assert stdout.delta == "[[[1 2 3]]]\n"


def test_equality_check_among_dataframes():
    """
    Tests that reactive signals holding pandas DataFrames only trigger effects when the DataFrame content changes.

    Verifies that setting a signal to a DataFrame with identical content does not notify effects, while setting it to a DataFrame with different content does.
    """
    get_df, set_df = create_signal(pd.DataFrame({"a": [0], "b": [1]}))
    with capture_stdout() as stdout, create_effect(lambda: print(get_df())):
        assert stdout.delta == "   a  b\n0  0  1\n"
        set_df(pd.DataFrame({"a": [0], "b": [1]}))
        assert stdout.delta == ""
        set_df(pd.DataFrame({"a": [1], "b": [2]}))
        assert stdout.delta == "   a  b\n0  1  2\n"


def test_context():
    """
    Tests that reactive states and effects respect their assigned contexts.

    Verifies that state updates only trigger effects within the same context, ensuring context isolation for reactive attributes and effect execution.
    """
    a = new_context()
    b = new_context()

    class Rect:
        x = State(1, context=a)
        y = State(2, context=b)

        @property
        def size(self):
            """
            Calculates the product of the x and y attributes.

            Returns:
                The result of multiplying self.x by self.y.
            """
            return self.x * self.y

    r = Rect()

    with capture_stdout() as stdout, a.effect(lambda: print(f"a{r.size}"), context=a), b.effect(lambda: print(f"b{r.size}"), context=b):
        assert stdout.delta == "a2\nb2\n"
        r.x = 3
        assert stdout.delta == "a6\n"
        r.y = 4
        assert stdout.delta == "b12\n"


def test_context_usage_with_reactive_namespace():
    """
    Tests that a Reactive dictionary within a custom context triggers effects on key updates.

    Verifies that effects registered in a specific context react to changes in a Reactive object created with that context, including correct handling of missing keys and subsequent updates.
    """
    c = new_context()
    dct = Reactive(context=c)

    with capture_stdout() as stdout:

        @c.effect
        def _():
            """
            Attempts to print the value for key 1 in the dictionary `dct`, printing a blank line if the key is missing.
            """
            try:
                print(dct[1])
            except KeyError:
                print()

        assert stdout.delta == "\n"
        dct[1] = 2
        assert stdout.delta == "2\n"


def test_reactive_proxy():
    """
    Tests the Proxy wrapper for reactive dictionary access and effect triggering.

    Verifies that executing code with exec in a Proxy context correctly accesses and prints reactive values, and that updates to the Proxy trigger effects. Also checks for known Python assertion behavior related to exec and context updates.
    """
    context = Proxy({"a": 123})
    with capture_stdout() as stdout, create_effect(lambda: exec("""class _: print(a)""", context.raw, context)):
        assert stdout.delta == "123\n"
        context["a"] = 234

        with raises(AssertionError):  # Because of https://github.com/python/cpython/issues/121306
            assert stdout.delta == "234\n", "(xfail)"
