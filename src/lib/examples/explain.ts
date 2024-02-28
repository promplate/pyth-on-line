import getTemplates from "../../templates";
import initPromplate from "../pyodide/entries";

export async function* explain(traceback: string, code: string) {
  const { AsyncChatGenerate } = await initPromplate();

  const context = await getTemplates();

  yield * AsyncChatGenerate({})(await context.ExplainError.arender({ ...context, traceback, code }), { model: "gpt-3.5-turbo-0125", temperature: 0 });
}
