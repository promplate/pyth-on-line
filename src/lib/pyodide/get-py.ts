import type { ClientOptions } from "openai";

import sources from "../../python";
import { getPyodide } from "./init";
import initCode from "./load-sources.py?raw";
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

export const getPy = cacheSingleton(async () => {
  const py = await getPyodide();
  py.globals.set("sources", py.toPy(sources));

  py.registerJsModule("openai", { OpenAI: PatchedOpenAI, version, __all__: [] });

  await py.runPythonAsync(initCode);

  return py;
});
