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

  try {
    const dependencies = parseToml(captured.join("\n")).dependencies;
    return { dependencies: Array.isArray(dependencies) ? dependencies.filter((dep): dep is string => typeof dep === "string") : [] };
  }
  catch {
    return { dependencies: [] as string[] };
  }
}

export function prependPep723(file: string, dependencies: string[]) {
  const headerLines = [
    "# /// script",
    "# dependencies = [",
    // JSON escapes work in TOML strings, but TOML also requires DEL to be escaped and valid Unicode scalars.
    ...dependencies.map(dep => `#   ${JSON.stringify(dep.toWellFormed()).replaceAll("\x7F", "\\u007f")},`),
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
