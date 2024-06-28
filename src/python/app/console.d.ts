export class Result {
  status: "complete" | "incomplete" | "syntax-error";
  formatted_error?: string;
  async get_repr(): Promise<string | undefined>;
}

class EnhancedConsole {
  stdout_callback(out: string);
  stderr_callback(err: string);
  pop(): void;
}

export class ConsoleAPI {
  complete(source: string): [string[], number];
  console: EnhancedConsole;
  async push(line: string): Result;
}
