import type { Inspection } from "../console/console";

export interface RunResult {
  out?: string;
  err?: string;
  repr?: string;
}

export class NotebookAPI {
  async run(source: string): Promise<RunResult>;
  inspect(source: string): Inspection ;
}
