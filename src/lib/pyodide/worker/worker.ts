/* eslint-disable no-restricted-globals */

/// <reference lib="webworker" />

import type { Task } from "./types";

import getPy from "..";

(self as unknown as SharedWorkerGlobalScope).addEventListener("connect", (event) => {
  const [port] = event.ports;
  port.addEventListener("message", handleMessage);
  port.start();
  port.postMessage("hello from worker");
});

async function handleMessage(event: MessageEvent<Task | object>) {
  if (typeof event.data === "object" && "id" in event.data) {
    const port = event.currentTarget as MessagePort;
    const { id, type, data } = event.data;
    // dispatch
    if (type === "eval") {
      runTask(id, port, handleEval(data));
    }
  }
  else {
    console.warn(event);
  }
}

function runTask(id: string, port: MessagePort, promise: Promise<any>) {
  promise
    .then(result => port.postMessage({ id, result }))
    .catch(error => port.postMessage({ id, error }));
}

async function handleEval(source: string) {
  // const { loadPyodide: getPy } = await import("pyodide");
  // const { getPyodide: getPy } = await import("../start/init");

  const py = await getPy();
  const result = await py.runPythonAsync(source);
  return String(result);
}
