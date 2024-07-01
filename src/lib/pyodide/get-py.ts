import type { ClientOptions } from "openai";

import console from "../../python/console";
import { loadChat } from "./explain";
import { getAtomicPy as getAtomicPyodide, getSetupModule } from "./init";
import * as env from "$env/static/public";
import { pyodideReady } from "$lib/stores";
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

export const getPy = cacheSingleton(async () => {
  const py = await getAtomicPyodide();
  const setupModule = await getSetupModule();

  py.registerJsModule("openai", { OpenAI: PatchedOpenAI, version, __all__: [] });

  setupModule(py.toPy(console), "console");

  pyodideReady.set(true);

  loadChat();

  return py;
});
