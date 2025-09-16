from pytest import raises
from reactivity import create_effect
from reactivity.collections import ReactiveMappingProxy, ReactiveSequenceProxy, ReactiveSetProxy
from utils import capture_stdout


def test_reactive_mapping_equality_check():
    proxy = ReactiveMappingProxy({}, check_equality=True)
    with capture_stdout() as stdout, create_effect(lambda: print(proxy.get("key", 0))):
        assert stdout.delta == "0\n"
        proxy["key"] = 1
        assert stdout.delta == "1\n"
        proxy["key"] = 1  # same value
        assert stdout.delta == ""
        proxy["key"] = 2
        assert stdout.delta == "2\n"


def test_reactive_mapping_no_equality_check():
    proxy = ReactiveMappingProxy({}, check_equality=False)
    with capture_stdout() as stdout, create_effect(lambda: print(proxy.get("key", 0))):
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

    with capture_stdout() as stdout, create_effect(lambda: print(sorted(proxy))):
        assert stdout.delta == "[1, 2, 3, 4]\n"
        proxy.add(4)
        assert stdout.delta == ""
        proxy.discard(2)
        assert stdout.delta == "[1, 3, 4]\n"

        assert proxy.isdisjoint({5, 6})
        assert not proxy.isdisjoint({3, 4})
        assert stdout.delta == ""


def test_reactive_mapping_repr():
    assert repr(ReactiveMappingProxy({"a": 1})) == "{'a': 1}"


def test_reactive_sequence_length():
    seq = ReactiveSequenceProxy([1, 2, 3])
    with capture_stdout() as stdout, create_effect(lambda: print(len(seq))):
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
    with capture_stdout() as stdout, create_effect(lambda: print(seq[1])):
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
    with capture_stdout() as stdout, create_effect(lambda: print(seq[-1])):
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


def test_reactive_sequence_slice_operations():
    seq = ReactiveSequenceProxy([1, 2, 3, 4])
    with capture_stdout() as stdout, create_effect(lambda: print(seq[1:2])):
        assert stdout.delta == "[2]\n"
        seq[-3:-1] = [20, 30]
        assert stdout.delta == "[20]\n"
        seq[-3] = 200
        assert stdout.delta == "[200]\n"
