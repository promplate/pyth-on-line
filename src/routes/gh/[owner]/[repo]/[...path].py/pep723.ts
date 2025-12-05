import { parse as parseToml } from "smol-toml";

export function parsePep723(content: string) {
  let inHeader = false;
  const captured: string[] = [];

  for (const line of content.split(/\r?\n/)) {
    if (/^#\s*\/\/\/\s*script\b/.test(line)) {
      inHeader = true;
      continue;
    }
    if (inHeader && /^#\s*\/\/\//.test(line))
      break;
    if (inHeader) {
      captured.push(line.replace(/^#\s?/, ""));
    }
    if (captured.length > 200)
      break;
  }

  if (!captured.length)
    return null;

  const block = captured.join("\n");
  const match = block.match(/dependencies\s*=\s*\[([\s\S]*?)\]/);
  if (!match)
    return { dependencies: [] as string[] };

  return { dependencies: splitArrayItems(match[1]) };
}

export function prependPep723(file: string, dependencies: string[]) {
  const escapedDeps = dependencies.map(dep => dep.replace(/"/g, "\\\""));
  const headerLines = [
    "# /// script",
    "# dependencies = [",
    ...escapedDeps.map(dep => `#   "${dep}",`),
    "# ]",
    "# ///",
    "",
    "",
  ];
  const header = headerLines.join("\n");

  if (file.startsWith("#!")) {
    const [shebang, ...rest] = file.split(/\r?\n/);
    return [shebang, header, rest.join("\n")].join("\n");
  }
  return `${header}${file}`;
}

export function findDependencies(pyprojects: Array<{ path: string; text: string | undefined }>) {
  for (const { path, text } of pyprojects) {
    if (!text)
      continue;
    const deps = parsePyprojectDeps(text);
    if (deps?.length)
      return { dependencies: deps, path };
  }
  return null;
}

function parsePyprojectDeps(pyproject: string) {
  try {
    const data = parseToml(pyproject) as { project?: { dependencies?: unknown } };
    const deps = data.project?.dependencies;
    if (!Array.isArray(deps))
      return null;
    const entries = deps
      .map(item => (typeof item === "string" ? item : String(item)))
      .map(entry => entry.trim())
      .filter(Boolean);
    return entries.length ? entries : null;
  }
  catch {
    return null;
  }
}

function splitArrayItems(raw: string) {
  const items: string[] = [];
  let current = "";
  let quote: "\"" | "'" | null = null;
  let escaped = false;

  for (const char of raw) {
    if (escaped) {
      current += char;
      escaped = false;
      continue;
    }
    if (char === "\\") {
      current += char;
      escaped = true;
      continue;
    }
    if (quote) {
      current += char;
      if (char === quote)
        quote = null;
      continue;
    }
    if (char === "\"" || char === "'") {
      quote = char;
      current += char;
      continue;
    }
    if (char === ",") {
      items.push(current.trim());
      current = "";
      continue;
    }
    current += char;
  }

  if (current.trim())
    items.push(current.trim());

  return items
    .map(item => item.replace(/^['"]|['"]$/g, ""))
    .map((item) => {
      const idx = item.indexOf("#");
      return (idx >= 0 ? item.slice(0, idx) : item).trim();
    })
    .filter(Boolean);
}
