export function patchSource(source: string) {
  return (
    source.includes(">>> ")
      ? source.split("\n").filter(line => line.startsWith(">>>") || line.startsWith("...") || !line.trim()).map(line => line.slice(4)).join("\n")
      : source
  );
}

export function reformatInputSource(source: string) {
  return source.split("\n").map((value, index) => (index ? "... " : ">>> ") + value).join("\n");
}
