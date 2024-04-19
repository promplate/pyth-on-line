import type { ClientOptions } from "openai";

import { pyodideReady } from "../stores";
import { dev } from "$app/environment";
import * as env from "$env/static/public";
import { cacheSingleton } from "$lib/utils/cache";
import { getEnv } from "$lib/utils/env";
import { withToast } from "$lib/utils/toast";

let indexURL: string | undefined;

if (typeof window === "undefined")
  indexURL = undefined;
else if (dev)
  indexURL = env.PUBLIC_PYODIDE_INDEX_URL ?? "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/";
else
  indexURL = env.PUBLIC_PYODIDE_INDEX_URL ?? "/pyodide/";

async function initPyodide() {
  const { loadPyodide } = await import("pyodide");
  const py = await loadPyodide({ indexURL, env: getEnv(), packages: ["micropip", "typing-extensions"] });
  pyodideReady.set(true);
  return py;
}

export const getPyodide = cacheSingleton(withToast(initPyodide, { loading: "loading pyodide runtime" }));

async function initPy() {
  const [py, { OpenAI }, version, { default: initCode }] = await Promise.all([
    getPyodide(),
    import("openai"),
    import("openai/version"),
    import("./init.py?raw"),
  ]);

  class PatchedOpenAI extends OpenAI {
    constructor(options: ClientOptions) {
      if (!options.apiKey)
        (options.apiKey = env.PUBLIC_OPENAI_API_KEY);
      if (!options.baseURL)
        options.baseURL = env.PUBLIC_OPENAI_BASE_URL;
      super(options);
    }
  }

  py.registerJsModule("openai", { OpenAI: PatchedOpenAI, version, __all__: [] });

  await withToast(py.runPythonAsync.bind(null, initCode), { loading: "installing extra python dependencies", duration: 300 })();

  return py;
}

export const getPy = cacheSingleton(initPy);

export async function initConsole() {
  const [py, { default: initConsoleCode }] = await Promise.all([getPyodide(), import("./console.py?raw")]);
  await py.runPythonAsync(initConsoleCode);
}
