import { existsSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const srcPath = "./src";

const files = readdirSync(srcPath, { recursive: true, withFileTypes: true }).filter(f => f.isFile()).map(f => `${f.parentPath}/${f.name}`);

for (const file of files) {
  if (!file.endsWith(".ts") && !file.endsWith(".svelte"))
    continue;

  const content = readFileSync(file, "utf-8");
  const lines = content.split("\n");

  for (const line of lines) {
    const importMatch = line.match(/import\s.*from\s*["'](.+)["']/);
    if (importMatch) {
      const modulePath = resolve(file, "..", importMatch[1]);

      if (existsSync(modulePath) && statSync(modulePath).isDirectory() && !existsSync(join(modulePath, "index.ts"))) {
        // generate dts
        writeFileSync(join(modulePath, "index.d.ts"), `export default {} as {${readdirSync(modulePath).map(name => `\n  ${JSON.stringify(name)}: string;`).join("")}\n}`, "utf-8");
        console.warn(`Generated ${modulePath}/index.d.ts`);
      }
    }
  }
}
