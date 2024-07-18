import type { Item } from "$lib/components/console/HeadlessConsole.svelte";
import type { PyAwaitable, PyProxy } from "pyodide/ffi";

export class Result<T> {
  status: "complete" | "incomplete" | "syntax-error";
  future: PyAwaitable & {
    add_done_callback: (callback: (future: Promise<T>) => any) => void ;
  };
}

export interface Inspection {
  class: string;
  value: string;
  type?: "class" | "exception";
}

export class ConsoleAPI extends PyProxy {
  complete(source: string): [string[], number];
  get_items(): Item[];
  incomplete: boolean;
  push(line: string): Result<any>;
  pop(): string;
  inspect(name: string): Inspection;
}
