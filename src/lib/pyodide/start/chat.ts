import type { ClientOptions } from "openai";

import chat from "../../../python/chat";
import { getPyodide, setupModule } from "./init";
import * as env from "$env/static/public";
import { cacheSingleton } from "$lib/utils/cache";
import { OpenAI } from "openai";
import * as version from "openai/version";

class PatchedOpenAI extends OpenAI {
  constructor(options: ClientOptions) {
    if (!options.apiKey)
      (options.apiKey = env.PUBLIC_OPENAI_API_KEY);
    if (!options.baseURL)
      options.baseURL = env.PUBLIC_OPENAI_BASE_URL;
    super(options);
  }
}

export const loadChat = cacheSingleton(async () => {
  const py = await getPyodide();
  py.registerJsModule("openai", { OpenAI: PatchedOpenAI, version, __all__: [] });
  await setupModule(chat, "chat");
  await py.pyimport("chat.install_requirements");
});

export async function* explain(traceback: string, code: string): AsyncGenerator<string> {
  const py = await getPyodide();
  await loadChat();
  const explain = py.pyimport("chat.explain").explain;
  yield * explain(traceback, code);
}
