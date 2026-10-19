import getPy from "..";

export async function* explain(traceback: string, code: string, signal?: AbortSignal): AsyncGenerator<string> {
  if (signal?.aborted)
    return;
  const py = await getPy({ chat: true });
  // Runtime loading is shared; a closed or superseded explainer must not start a new request.
  if (signal?.aborted)
    return;
  const explain = py.pyimport("chat.explain.explain");
  yield* explain(traceback, code);
}
