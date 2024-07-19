import type { PyProxy } from "pyodide/ffi";

import patches from "../../../python/patches";
import { indexURL, preloadPackages } from "../common";
import loader from "./loader.py?raw";
import { dev } from "$app/environment";
import { cacheSingleton } from "$lib/utils/cache";
import { getEnv } from "$lib/utils/env";
import { withToast } from "$lib/utils/toast";
import { toast } from "svelte-sonner";

const getMinimalPyodide = cacheSingleton(withToast({ loading: "loading pyodide runtime" })(async () => {
  const { loadPyodide } = await import("pyodide");
  const py = await loadPyodide({ indexURL, env: getEnv(), packages: preloadPackages, args: dev ? [] : ["-O"] });
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
