import getPy from "..";

export async function* explain(traceback: string, code: string): AsyncGenerator<string> {
  const py = await getPy({ chat: true });
  const explain = py.pyimport("chat.explain.explain");
  yield* explain(traceback, code);
}
