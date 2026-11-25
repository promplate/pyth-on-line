import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { createServer } from "node:http";
import { join } from "node:path";

import { loadPyodide } from "pyodide";

const wheelDir = process.argv[2];
const wheel = readdirSync(wheelDir).find(name => name.startsWith("micropip-") && name.endsWith(".whl"));
assert(wheel);
const indexRequests = [];
const server = createServer((req, res) => {
  if (req.url === `/${wheel}`) {
    res.end(readFileSync(join(wheelDir, wheel)));
    return;
  }
  indexRequests.push(req.url);
  res.writeHead(404).end();
});

await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
try {
  const url = `http://127.0.0.1:${server.address().port}`;
  const customIndex = process.argv.includes("--custom-index");
  const py = await loadPyodide({ env: customIndex ? { PYPI_INDEX_URL: `${url}/simple` } : {} });
  await py.loadPackage("packaging");
  await py.loadPackage(`${url}/${wheel}`);

  // Only browser-specific UI plumbing is stubbed; all installs use real WASM Python.
  globalThis.window = { prompt: () => "", close: () => {} };
  for (const path of ["common/patches.py", "common/imports.py", "common/package.py", "common/toast.py", "chat/__init__.py"]) {
    py.FS.mkdirTree(`/app/${path.split("/")[0]}`);
    py.FS.writeFile(`/app/${path}`, readFileSync(`src/python/${path}`));
  }

  await py.runPythonAsync(`
import sys
from importlib import reload
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import micropip
from pyodide.console import PyodideConsole
from pyodide_js import loadedPackages

sys.path.insert(0, "/app")
events = []
toast = SimpleNamespace(
    loading=lambda message, **kwargs: events.append(("loading", message)),
    success=lambda message, **kwargs: events.append(("success", message)),
    error=lambda message, **kwargs: events.append(("error", message)),
)
import common.patches
from common.imports import find_packages_to_install

print("micropip", micropip.__version__)
assert find_packages_to_install("import yaml; import sys; import not_a_bundled_package") == ["pyyaml"]
console = PyodideConsole()
await console.push("import yaml")
assert console.globals["yaml"].safe_load("a: 1") == {"a": 1}
assert find_packages_to_install("import yaml") == []
assert events == [("loading", "pip install pyyaml"), ("success", "pip install pyyaml")]

# The chat bootstrap uses the real installer and registry, but its unrelated
# OpenAI SDK / HTTP patch is replaced with a spy.
shim = ModuleType("promplate_pyodide")
shim.patch_all = AsyncMock()
sys.modules["promplate_pyodide"] = shim
import chat
await chat.install_requirements
assert {"promplate", "promplate-pyodide"} <= loadedPackages.to_py().keys()
assert shim.patch_all.await_count == 1
assert events[-2:] == [
    ("loading", "pip install promplate promplate-pyodide"),
    ("success", "pip install promplate promplate-pyodide"),
]
previous = events[:]
await reload(chat).install_requirements
assert events == previous
assert shim.patch_all.await_count == 2
`);

  if (customIndex) {
    assert(!indexRequests.some(path => path.startsWith("/simple/pyyaml")), "Pyodide lockfile must be searched before the mirror");
    assert(indexRequests.some(path => path.startsWith("/simple/promplate/")), "Custom mirror must be tried before PyPI");
  }
  else {
    assert.equal(indexRequests.length, 0);
  }
}
finally {
  server.closeAllConnections();
  server.close();
}
