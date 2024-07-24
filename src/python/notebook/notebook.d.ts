import type { Inspection } from "../console/console";
import type { PyProxy } from "pyodide/ffi";

interface Item {
  type: "out" | "err" | "repr";
  text: string;
}

type Callback = (items: Item[]) => any;

export class NotebookAPI extends PyProxy {
  async run(source: string, sync: Callback, console = false): Promise<void>;
  inspect(source: string): Inspection;
  is_python(source: string): boolean;
}
