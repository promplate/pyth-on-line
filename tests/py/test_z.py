import pytest


@pytest.fixture
def zzz():
    yield 123


def test_fixture(zzz):
    assert zzz == 123


@pytest.mark.xfail(raises=ValueError)
def test_xfail():
    raise ValueError
