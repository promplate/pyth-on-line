import type { UUID } from "./types";

import { cacheSingleton } from "$lib/utils/cache";

const getWorker = cacheSingleton(() => {
  const worker = new SharedWorker(new URL("./worker", import.meta.url), { name: "pyodide", type: "module" });
  worker.port.addEventListener("message", handleMessage);
  worker.port.start();
  worker.port.postMessage("hello from main thread");
  return worker;
});

const pendingTasks = new Map<UUID, [(value: any) => void, (reason: any) => void]>();

async function handleMessage(event: MessageEvent) {
  if (typeof event.data === "object" && "id" in event.data) {
    const data: { id: UUID } & ({ result: any } | { error: any }) = event.data;
    const [resolve, reject] = pendingTasks.get(data.id)!;
    "error" in data ? reject(data.error) : resolve(data.result);
    pendingTasks.delete(data.id);
  }
}

export function evalPython(source: string) {
  const worker = getWorker();
  const id = crypto.randomUUID();
  const task = new Promise((resolve, reject) => {
    pendingTasks.set(id, [resolve, reject]);
  });
  worker.port.postMessage({ id, data: source, type: "eval" });
  return task;
}
