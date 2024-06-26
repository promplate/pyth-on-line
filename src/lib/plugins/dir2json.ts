import { type Dirent, existsSync, promises as fs } from "node:fs";
import path from "node:path";
import { type PluginOption, normalizePath } from "vite";

export default (): PluginOption => {
  return {
    name: "dir-as-json",

    async resolveId(source, importer) {
      if (source.endsWith("?dir2json")) {
        return null;
      }

      const dirPath = path.join(path.dirname(importer ?? ""), source);

      if (!existsSync(dirPath) || !(await fs.stat(dirPath)).isDirectory()) {
        return null;
      }

      for (const name of ["index.ts", "index.js"]) { // normal module
        if (existsSync(path.join(dirPath, name))) {
          return null;
        }
      }

      return `\0${dirPath}?dir2json`;
    },

    async load(id) {
      if (!id.endsWith("?dir2json")) {
        return null;
      }

      const dirPath = id.slice(1, -9); // remove trailing '?dir2json' and leading '\0'

      const dirEntries: [string, Dirent[]][] = [["", await fs.readdir(dirPath, { withFileTypes: true, encoding: "utf-8" })]];

      const files: Record<string, string> = {};

      const promises: Promise<void>[] = [];

      while (dirEntries.length) {
        const [parentPath, entries] = dirEntries.pop()!;
        const absoluteParentPath = path.join(dirPath, parentPath);
        promises.push(...entries.map(async (entry) => {
          if (entry.isFile() && !entry.name.endsWith(".pyi") && !entry.name.endsWith(".d.ts")) {
            const filePath = path.join(absoluteParentPath, entry.name);
            const relativePath = path.relative(dirPath, filePath);
            const content = await fs.readFile(filePath, "utf-8");
            files[normalizePath(relativePath)] = content; // \ -> /
          }
          else if (entry.isDirectory()) {
            dirEntries.push([path.join(parentPath, entry.name), await fs.readdir(path.join(absoluteParentPath, entry.name), { withFileTypes: true, encoding: "utf-8" })]);
          }
        }));
        await Promise.all(promises);
        promises.length = 0;
      }
      await Promise.all(promises);
      return `export default ${JSON.stringify(files)};`;
    },
  };
};
