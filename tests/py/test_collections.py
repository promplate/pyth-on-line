from collections import UserList
from typing import TypedDict

from pytest import raises
from reactivity import effect
from reactivity.collections import ReactiveMappingProxy, ReactiveSequenceProxy, ReactiveSetProxy, reactive, reactive_object_proxy
from utils import capture_stdout


def test_reactive_mapping_equality_check():
    proxy = ReactiveMappingProxy({}, check_equality=True)
    with capture_stdout() as stdout, effect(lambda: print(proxy.get("key", 0))):
        assert stdout.delta == "0\n"
        proxy["key"] = 1
        assert stdout.delta == "1\n"
        proxy["key"] = 1  # same value
        assert stdout.delta == ""
        proxy["key"] = 2
        assert stdout.delta == "2\n"


def test_reactive_mapping_no_equality_check():
    proxy = ReactiveMappingProxy({}, check_equality=False)
    with capture_stdout() as stdout, effect(lambda: print(proxy.get("key", 0))):
        assert stdout.delta == "0\n"
        proxy["key"] = 1
        assert stdout.delta == "1\n"
        proxy["key"] = 1  # same value, still notifies
        assert stdout.delta == "1\n"


def test_reactive_set_proxy():
    proxy = ReactiveSetProxy(raw := {1, 2, 3})

    assert 1 in proxy
    assert len(proxy) == 3

    proxy.add(4)
    assert len(proxy) == 4
    assert 4 in proxy
    assert 4 in raw
    proxy.add(3)
    assert len(proxy) == 4

    with capture_stdout() as stdout, effect(lambda: print(sorted(proxy))):
        assert stdout.delta == "[1, 2, 3, 4]\n"
        proxy.add(4)
        assert stdout.delta == ""
        proxy.discard(2)
        assert stdout.delta == "[1, 3, 4]\n"

        assert proxy.isdisjoint({5, 6})
        assert not proxy.isdisjoint({3, 4})
        assert stdout.delta == ""


def test_reactive_set_no_equality_check():
    s = reactive(set(), check_equality=False)
    with capture_stdout() as stdout, effect(lambda: print(s)):
        assert stdout.delta == "set()\n"
        s.add(1)
        assert stdout.delta == "{1}\n"
        s.add(1)
        assert stdout.delta == "{1}\n"
        s.pop()
        assert stdout.delta == "set()\n"
        with raises(KeyError):
            s.pop()
        assert stdout.delta == ""


def test_reactive_mapping_repr():
    assert repr(ReactiveMappingProxy({"a": 1})) == "{'a': 1}"


def test_reactive_sequence_length():
    seq = ReactiveSequenceProxy([1, 2, 3])
    with capture_stdout() as stdout, effect(lambda: print(len(seq))):
        assert stdout.delta == "3\n"
        del seq[:]
        assert stdout.delta == "0\n"
        seq.extend([1, 2, 3, 4])
        assert stdout.delta == "4\n"
        seq.pop()
        seq.pop()
        assert stdout.delta == "3\n2\n"
        seq.reverse()
        assert stdout.delta == ""
        assert seq == [2, 1]
        seq[0:0] = [3, 4]
        assert stdout.delta == "4\n"
        seq.remove(3)
        assert stdout.delta == "3\n"


def test_reactive_sequence_setitem():
    seq = ReactiveSequenceProxy([0, 0], check_equality=True)
    with capture_stdout() as stdout, effect(lambda: print(seq[1])):
        assert stdout.delta == "0\n"
        seq.insert(0, 1)
        assert stdout.delta == ""
        seq.insert(0, 1)
        assert stdout.delta == "1\n"
        seq[1] = 2
        assert stdout.delta == "2\n"
        with raises(IndexError):
            seq.clear()


def test_reactive_sequence_negative_index():
    seq = ReactiveSequenceProxy([0])
    with capture_stdout() as stdout, effect(lambda: print(seq[-1])):
        assert stdout.delta == "0\n"
        seq.append(1)
        assert stdout.delta == "1\n"
        seq.extend([0, 1])
        assert stdout.delta == ""
        seq.pop()
        assert stdout.delta == "0\n"
        seq[-1] = 20
        assert stdout.delta == "20\n"
        seq.insert(0, 10)
        assert stdout.delta == ""


def test_reactive_sequence_negative_indices():
    seq = ReactiveSequenceProxy([0, 1])
    with capture_stdout() as stdout, effect(lambda: print(seq[-3:-1])):
        seq.append(2)
        seq.append(2)
        seq.append(2)
        assert stdout.delta == "[0]\n[0, 1]\n[1, 2]\n[2, 2]\n"
        seq.append(2)
        assert stdout.delta == ""
    seq = ReactiveSequenceProxy([0, 0], check_equality=False)
    with capture_stdout() as stdout, effect(lambda: print(seq[-2:])):
        seq.append(0)
        assert stdout == "[0, 0]\n[0, 0]\n"


def test_reactive_sequence_slice_operations():
    seq = ReactiveSequenceProxy([1, 2, 3, 4])
    with capture_stdout() as stdout, effect(lambda: print(seq[1:2])):
        assert stdout.delta == "[2]\n"
        seq[-3:-1] = [20, 30]
        assert stdout.delta == "[20]\n"
        seq[-3] = 200
        assert stdout.delta == "[200]\n"


def test_reactive_object_proxy():
    from argparse import Namespace

    obj = reactive_object_proxy(raw := Namespace(foo=1))

    with capture_stdout() as stdout, effect(lambda: print(obj.foo)):
        assert stdout.delta == "1\n"
        obj.foo = 10
        assert stdout.delta == "10\n"
        obj.__dict__["foo"] = 100
        assert stdout.delta == "100\n"

    assert str(obj) == str(raw)


def test_reactive_object_proxy_accessing_properties():
    class Rect:
        def __init__(self):
            self._a = 1
            self._b = 2

        @property
        def a(self):
            return self._a

        @a.setter
        def a(self, value: int):
            self._a = value

        @property
        def b(self):
            return self._b

        @b.setter
        def b(self, value: int):
            self._b = value

        @property
        def size(self):
            return self.a * self.b

    rect = reactive_object_proxy(Rect())

    with capture_stdout() as stdout, effect(lambda: print(rect.size)):
        assert stdout.delta == "2\n"
        rect.a = 10
        assert stdout.delta == "20\n"
        rect.b = 20
        assert stdout.delta == "200\n"


def test_reactive_class_proxy():
    @reactive
    class Ref:
        value = 1

    assert repr(Ref) == str(Ref) == "<class 'test_collections.test_reactive_class_proxy.<locals>.Ref'>"

    with capture_stdout() as stdout, effect(lambda: print(Ref.value)):
        assert stdout.delta == "1\n"
        Ref.value = 2
        assert stdout.delta == "2\n"

    obj = Ref()

    with capture_stdout() as stdout, effect(lambda: print(obj.value)):
        assert stdout.delta == "2\n"
        obj.value = 3
        assert stdout.delta == "3\n"
        del obj.value
        assert stdout.delta == "2\n"


def test_reactive_router():
    assert isinstance(reactive({}), ReactiveMappingProxy)
    assert isinstance(reactive(set()), ReactiveSetProxy)
    assert isinstance(reactive([]), ReactiveSequenceProxy)

    class A: ...

    assert reactive(A) is not A
    assert reactive(a := A()) is not a

    class B(TypedDict): ...

    assert isinstance(reactive(B)(), ReactiveMappingProxy)

    class C(UserList): ...

    assert isinstance(reactive(C)(), ReactiveSequenceProxy)

    class D(UserList): ...

    assert isinstance(reactive(D()), ReactiveSequenceProxy)

    class E(set):
        def __new__(cls):
            return super().__new__(cls)

    assert isinstance(reactive(E()), ReactiveSetProxy)
