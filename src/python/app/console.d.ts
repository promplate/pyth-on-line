import type { PyProxy } from "pyodide/ffi";

export class Result<T> {
  status: "complete" | "incomplete" | "syntax-error";
  future: Promise<T>;
  formatted_error?: string;
  async get_repr(): Promise<string | undefined>;
}

class EnhancedConsole {
  stdout_callback(out: string);
  stderr_callback(err: string);
  pop(): void;
}

export class ConsoleAPI extends PyProxy {
  complete(source: string): [string[], number];
  console: EnhancedConsole;
  push(line: string): Result<any>;
}
