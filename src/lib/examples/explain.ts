import { getPy } from "../pyodide";

export async function* explain(traceback: string, code: string) {
  const py = await getPy();
  await py.globals.get("background_tasks");
  const explain = py.globals.get("explain");
  yield * explain(traceback, code);
}
