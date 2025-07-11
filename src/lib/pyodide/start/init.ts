import type { PyProxy } from "pyodide/ffi";

import common from "../../../python/common";
import watchfiles from "../../../python/watchfiles";
import { indexURL, preloadPackages } from "../common";
import { setupWatcher } from "./fs";
import loader from "./loader.py?raw";
import { dev } from "$app/environment";
import { cacheSingleton } from "$lib/utils/cache";
import { getEnv } from "$lib/utils/env";
import { withToast } from "$lib/utils/toast";
import { toast } from "svelte-sonner";

const getMinimalPyodide = cacheSingleton(withToast({ loading: "加载 Pyodide 运行时" })(async () => {
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
  await setupModule(common, "common");
  await setupModule(watchfiles, "watchfiles");
  py.pyimport("common.patches");
  setupWatcher(py);
  return py;
});
