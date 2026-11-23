"""Verify a built hottest wheel in an isolated environment."""

from pathlib import Path
from sysconfig import get_path
from tempfile import TemporaryDirectory

import hottest
from hottest._vendored_reactivity.hmr.core import HMR_CONTEXT, BaseReloader
from watchfiles import Change

assert hottest.__file__ is not None
installed = Path(hottest.__file__).resolve().parent
assert installed.is_relative_to(Path(get_path("purelib")).resolve()), installed

# Detect missing links when reactivity files are added or renamed.
source = Path(__file__).resolve().parents[1] / "packages/hmr/reactivity"
vendored = installed / "_vendored_reactivity"
expected = {path.relative_to(source): path.read_bytes() for path in source.rglob("*.py")}
actual = {path.relative_to(vendored): path.read_bytes() for path in vendored.rglob("*.py")}
assert actual == expected, "The wheel must contain the complete, unmodified reactivity package"

with TemporaryDirectory() as directory:
    entry = Path(directory) / "subject.py"
    entry.write_text("value = 1\n", encoding="utf-8")
    reloader = BaseReloader(str(entry), includes=(directory,))
    reloader.run_entry_file()
    observed = []

    def check_value():
        observed.append(reloader.entry_module.value)

    with HMR_CONTEXT.effect(lambda: hottest.run_test(check_value, {})):
        assert observed == [1], observed
        entry.write_text("value = 2\n", encoding="utf-8")
        reloader.on_events([(Change.modified, str(entry))])
        assert observed == [1, 2], observed

print(f"hottest package smoke passed: {len(expected)} vendored files and in-process reload")
