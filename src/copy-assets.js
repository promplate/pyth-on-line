import { Buffer } from "node:buffer";
import * as fs from "node:fs";
import { writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";

const require = createRequire(resolve("node_modules"));

const pyodideDir = dirname(require.resolve("pyodide"));
const targetDir = resolve(join("static", "pyodide"));

const lock = fs.readFileSync(join(pyodideDir, "pyodide-lock.json"), "utf-8");
const { version } = JSON.parse(fs.readFileSync(join(pyodideDir, "package.json"), "utf-8"));

async function downloadPackage(slug) {
  const path = join(pyodideDir, slug);
  if (!fs.existsSync(path)) {
    const res = await fetch(`https://cdn.jsdelivr.net/pyodide/v${version}/full/${slug}`);
    const data = await res.arrayBuffer();
    await writeFile(path, Buffer.from(data));
  }
}

async function preparePackages(names) {
  const promises = [];

  for (const url of lock.matchAll(/"[^"\s]+\.whl"/g)) {
    const slug = url[0].slice(1, -1);

    if (names.some(name => slug.includes(name)))
      promises.push(downloadPackage(slug));
  }

  await Promise.all(promises);
}

if (process.env.NODE_ENV !== "production" || !process.env.PUBLIC_PYODIDE_INDEX_URL)
  await preparePackages(["micropip", "packaging", "typing_extensions"]);

if (!fs.existsSync(targetDir)) {
  fs.rmSync(targetDir, { force: true });
  fs.symlinkSync(pyodideDir, targetDir);
}
