import getTemplates from "../../templates";
import initPromplate from "../pyodide/entries";
import * as env from "$env/static/public";

export async function* explain(traceback: string, code: string) {
  const { AsyncChatGenerate } = await initPromplate();

  const context = await getTemplates();

  yield * AsyncChatGenerate({})(await context.ExplainError.arender({ ...context, traceback, code }), { model: env.PUBLIC_LLM_MODEL ?? "gpt-3.5-turbo-0125", temperature: 0 });
}
