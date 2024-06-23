import type { ClientOptions } from "openai";

import { pyodideReady } from "../stores";
import initCode from "./load-sources.py?raw";
import { dev } from "$app/environment";
import * as env from "$env/static/public";
import { cacheSingleton } from "$lib/utils/cache";
import { getEnv } from "$lib/utils/env";
import { withToast } from "$lib/utils/toast";
import { OpenAI } from "openai";
import * as version from "openai/version";

let indexURL: string | undefined;

if (typeof window === "undefined")
  indexURL = undefined;
else if (dev)
  indexURL = env.PUBLIC_PYODIDE_INDEX_URL ?? "https://cdn.jsdelivr.net/pyodide/v0.26.1/full/";
else
  indexURL = env.PUBLIC_PYODIDE_INDEX_URL ?? "/pyodide/";

async function initPyodide() {
  const { loadPyodide } = await import("pyodide");
  const py = await loadPyodide({ indexURL, env: getEnv(), packages: ["micropip", "typing-extensions"] });
  py.globals.set("with_toast", withToast);
  pyodideReady.set(true);
  return py;
}

const getPyodide = cacheSingleton(withToast({ loading: "loading pyodide runtime" })(initPyodide));

class PatchedOpenAI extends OpenAI {
  constructor(options: ClientOptions) {
    if (!options.apiKey)
      (options.apiKey = env.PUBLIC_OPENAI_API_KEY);
    if (!options.baseURL)
      options.baseURL = env.PUBLIC_OPENAI_BASE_URL;
    super(options);
  }
}

async function getSources(): Promise<Record<string, string>> {
  return await (await fetch("/sources")).json();
}

export const getPy = cacheSingleton(async () => {
  const [py, sources] = await Promise.all([getPyodide(), getSources()]);
  py.globals.set("sources", py.toPy(sources));

  py.registerJsModule("openai", { OpenAI: PatchedOpenAI, version, __all__: [] });

  await py.runPythonAsync(initCode);

  pyodideReady.set(true);

  return py;
});
