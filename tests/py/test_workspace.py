import sys
from contextlib import closing
from importlib import import_module
from pathlib import Path
from runpy import run_path
from types import ModuleType, SimpleNamespace

import __main__


def test_workspace_modules_are_unloaded(monkeypatch, tmp_path):
    def setup_module(sources, *, base_path):
        for name, content in sources.items():
            file = base_path / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(content)

    def unexpected_lookup(name):
        raise AssertionError(name)

    external = ModuleType("workspace_external")
    external.__file__ = str(tmp_path / "workspace_external.py")
    external.__getattr__ = unexpected_lookup
    monkeypatch.setitem(sys.modules, "workspace_external", external)
    monkeypatch.setitem(sys.modules, "workspace_missing", None)
    monkeypatch.setitem(sys.modules, "js", SimpleNamespace(console=SimpleNamespace(error=lambda *_: None)))
    monkeypatch.setattr(__main__, "setup_module", setup_module, raising=False)
    api = run_path(str(Path(__file__).parents[2] / "src/python/workspace/__init__.py"))["WorkspaceAPI"]
    original_cwd = Path.cwd()

    for value in ("first", "second"):
        sources = {
            "workspace_sample.py": f"value = {value!r}",
            "workspace_package/__init__.py": "",
            "workspace_package/child.py": f"value = {value!r}",
            "workspace_namespace/child.py": f"value = {value!r}",
            "workspace_external.py": "value = 'shadowed'",
        }
        with closing(api(sources)) as workspace:
            for name in ("workspace_sample", "workspace_package.child", "workspace_namespace.child"):
                assert import_module(name).value == value
            assert import_module("workspace_external") is external
            directory = workspace.directory.name

        assert Path.cwd() == original_cwd
        assert directory not in sys.path
        assert not Path(directory).exists()
        for name in ("workspace_sample", "workspace_package", "workspace_package.child", "workspace_namespace", "workspace_namespace.child"):
            assert name not in sys.modules
        assert sys.modules["workspace_external"] is external
        assert sys.modules["workspace_missing"] is None
