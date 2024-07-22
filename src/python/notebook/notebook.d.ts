import type { Inspection } from "../console/console";

interface Item {
  type: "out" | "err" | "repr";
  text: string;
}

type Callback = (items: Item[]) => any;

export class NotebookAPI {
  async run(source: string, sync: Callback): Promise<void>;
  inspect(source: string): Inspection;
  is_python(source: string): boolean;
}
