import type { PyProxy } from "pyodide/ffi";

export class WorkspaceAPI extends PyProxy {
  close(): void;
}
