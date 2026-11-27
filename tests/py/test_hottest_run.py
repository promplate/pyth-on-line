from sys import version_info
from typing import TYPE_CHECKING

from hottest import run_test
from pytest import mark

if TYPE_CHECKING:
    from pathlib import Path


@mark.skipif(version_info < (3, 14), reason="requires deferred annotations")
def test_fixture_annotation_with_type_checking_import(tmp_path):
    def example(path: Path):
        return path

    assert run_test(example, {"path": lambda: tmp_path}) == tmp_path
