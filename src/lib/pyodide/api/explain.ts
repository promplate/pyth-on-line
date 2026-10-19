import type { PyAsyncGenerator, PyAwaitable, PyCallable } from "pyodide/ffi";

import getPy from "..";

export async function* explain(traceback: string, code: string, signal?: AbortSignal): AsyncGenerator<string> {
  if (signal?.aborted)
    return;
  const py = await getPy({ chat: true });
  // Runtime loading is shared; a closed or superseded explainer must not start a new request.
  if (signal?.aborted)
    return;
  const explain = py.pyimport("chat.explain.explain") as PyCallable;
  const schedule = py.pyimport("asyncio.ensure_future") as PyCallable;
  const stream = explain(traceback, code) as PyAsyncGenerator;
  let task: PyAwaitable | undefined;
  // Cancelling the Python task interrupts a pending read, even before the next delta arrives.
  const cancel = () => task?.cancel();
  signal?.addEventListener("abort", cancel, { once: true });
  try {
    while (!signal?.aborted) {
      const next = stream.__anext__();
      try {
        task = schedule(next) as PyAwaitable;
      }
      finally {
        next.destroy();
      }
      try {
        // Awaiting a PyProxy destroys it; keep the owning proxy alive for cancellation.
        yield await (task.copy() as PyAwaitable);
      }
      catch (e) {
        if (e instanceof Error && "type" in e && e.type === "StopAsyncIteration")
          return;
        throw e;
      }
      finally {
        task.destroy();
        task = undefined;
      }
    }
  }
  finally {
    signal?.removeEventListener("abort", cancel);
    try {
      await stream.return(undefined);
    }
    finally {
      stream.destroy();
      schedule.destroy();
      explain.destroy();
    }
  }
}
