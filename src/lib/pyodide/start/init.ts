import type { PyProxy } from "pyodide/ffi";

import patches from "../../../python/patches";
import loader from "./loader.py?raw";
import { dev } from "$app/environment";
import * as env from "$env/static/public";
import { cacheSingleton } from "$lib/utils/cache";
import { getEnv } from "$lib/utils/env";
import { withToast } from "$lib/utils/toast";
import { toast } from "svelte-sonner";

let indexURL: string | undefined;

if (typeof window === "undefined")
  indexURL = undefined;
else if (dev)
  indexURL = env.PUBLIC_PYODIDE_INDEX_URL ?? "https://cdn.jsdelivr.net/pyodide/v0.26.1/full/";
else
  indexURL = env.PUBLIC_PYODIDE_INDEX_URL ?? "/pyodide/";

const getMinimalPyodide = cacheSingleton(withToast({ loading: "loading pyodide runtime" })(async () => {
  const { loadPyodide } = await import("pyodide");
  const py = await loadPyodide({ indexURL, env: getEnv(), packages: ["micropip"], args: dev ? [] : ["-O"] });
  py.globals.set("toast", toast);
  return py;
}));

const getSetupModule = cacheSingleton(async () => {
  const py = await getMinimalPyodide();
  return py.runPython(loader) as (sources: Record<string, string>, moduleName: string) => PyProxy;
});

export async function setupModule(sources: Record<string, string>, moduleName: string) {
  const setupModule = await getSetupModule();
  const py = await getMinimalPyodide();
  setupModule(py.toPy(sources), moduleName);
}

export const getPyodide = cacheSingleton(async () => {
  const py = await getMinimalPyodide();
  await setupModule(patches, "patches");
  py.pyimport("patches.patches");
  return py;
});
