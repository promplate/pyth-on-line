export type SourceRef = { id: string; hidden?: boolean; wait?: boolean } | string;

export interface Source { source: string; hidden?: boolean; wait?: boolean };

export function refToSource(ref: SourceRef): Source {
  return (typeof ref === "string") ? { source: loadSource(ref) } : { source: loadSource(ref.id), hidden: ref.hidden ?? false, wait: ref.wait ?? false };
}

export function saveSource(key: string, source: string) {
  window.cache.set(key, source);
}

function loadSource(key: string): string {
  return window.cache.get(key) as string;
}

export function h(strings: TemplateStringsArray, ..._: any[]): SourceRef {
  return { id: strings[0], hidden: true };
}

export function w(strings: TemplateStringsArray, ..._: any[]): SourceRef {
  return { id: strings[0], wait: true };
}
