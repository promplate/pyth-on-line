import { findDependencies, prependPep723 } from "../../src/routes/gh/[owner]/[repo]/[...path].py/pep723";
import assert from "node:assert/strict";
// eslint-disable-next-line test/no-import-node-test -- Use Bun's node:test support without adding a test dependency.
import { test } from "node:test";
import { parse as parseToml } from "smol-toml";

const cases: Array<[string, string[]]> = [
  ["empty dependencies", []],
  ["version constraints and markers", ["requests>=2", "rich; python_version >= \"3.11\""]],
  ["literal backslashes", [String.raw`package @ file:///C:\temp\package`, "package\\"]],
  ["backslashes before quotes", [String.raw`package\", \"injected`]],
  ["line breaks and script delimiters", ["package\n# ///\ninjected = True\n#", "package\r\ninjected = True\r#"]],
  ["control characters", Array.from({ length: 32 }, (_, code) => `package${String.fromCharCode(code)}end`).concat("package\x7Fend")],
];

for (const [name, dependencies] of cases) {
  test(`prependPep723 preserves ${name} inside comments`, () => {
    const file = "print('original')\n";
    const content = prependPep723(file, dependencies);
    assert.ok(content.endsWith(file));
    const lines = content.slice(0, -file.length).trimEnd().split(/\r?\n/);
    assert.equal(lines[0], "# /// script");
    assert.equal(lines.at(-1), "# ///");
    assert.ok(lines.every(line => line.startsWith("# ")));
    assert.deepEqual({ ...parseToml(lines.slice(1, -1).map(line => line.slice(2)).join("\n")) }, { dependencies });
  });
}

test("pyproject dependencies cannot introduce executable Python lines", () => {
  const pyproject = "[project]\ndependencies = ['''package\ninjected = True\n#''']";
  const found = findDependencies([{ path: "pyproject.toml", text: pyproject }]);
  assert.ok(found);
  const content = prependPep723("original = True\n", found.dependencies);
  assert.deepEqual(content.split(/\r?\n/).filter(line => line && !line.startsWith("#")), ["original = True"]);
});

test("prependPep723 keeps the shebang first", () => {
  const content = prependPep723("#!/usr/bin/env python\r\nprint('original')\r\n", ["requests"]);
  assert.ok(content.startsWith("#!/usr/bin/env python\n# /// script\n"));
  assert.ok(content.endsWith("\n\nprint('original')\n"));
});
