import type { PyProxy } from "pyodide/ffi";

export class WorkspaceAPI extends PyProxy {
  close(): void;
  sync(sources: Record<string, string>, reload = true): void;
  save(path: string, content: string, reload = true): string | void;
}
