export function packMarkdown(files: Record<string, string>) {
  return Object.entries(files).map(([path, text]) => `\`${path}\`\n\n\`\`\`${path.split(".").at(-1) ?? ""}\n${text.replaceAll("\r", "").trimEnd()}\n\`\`\``).join("\n\n---\n\n");
}

export function packXML(files: Record<string, string>) {
  return Object.entries(files).map(([path, content]) => `<file path="${path}">\n${content.replaceAll("\r", "").trimEnd()}\n</file>`).join("\n\n");
}
