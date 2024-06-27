import type { PyProxy } from "pyodide/ffi";

export class Result extends PyProxy {
  status: "complete" | "incomplete" | "syntax-error";
  formatted_error?: string;
  future: Promise<any>;
  async get_value_and_repl(): Promise<[PyProxy | null, string]>;
}

class PyodideConsole extends PyProxy {
  stdout_callback(out: string);
  stderr_callback(err: string);
}

export class Console {
  complete(source: string): [string[], number];
  console: PyodideConsole;
  async push(line: string): Result;
}
