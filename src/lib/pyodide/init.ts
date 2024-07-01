import type { PyProxy } from "pyodide/ffi";

import patches from "../../python/patches";
import source from "./load-sources.py?raw";
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

export const getMinimalPyodide = cacheSingleton(withToast({ loading: "loading pyodide runtime" })(async () => {
  const { loadPyodide } = await import("pyodide");
  const py = await loadPyodide({ indexURL, env: getEnv(), packages: ["micropip"], args: dev ? [] : ["-O"] });
  py.globals.set("with_toast", withToast);
  py.globals.set("toast", toast);
  return py;
}));

export const getSetupModule = cacheSingleton(async () => {
  const py = await getMinimalPyodide();
  return py.runPython(source) as (sources: Record<string, string>, moduleName: string) => PyProxy;
});

export const getAtomicPy = cacheSingleton(async () => {
  const setupModule = await getSetupModule();
  const py = await getMinimalPyodide();
  setupModule(py.toPy(patches), "patches");
  py.pyimport("patches.patches");
  return py;
});
