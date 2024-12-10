export type UUID = ReturnType<Crypto["randomUUID"]>;

interface BaseTask {
  id: UUID;
  type: string;
  data: any;
}

export interface EvalTask extends BaseTask {
  type: "eval";
  data: string;
}

export type Task = EvalTask;
