import { pyodideReady } from "../stores";
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

async function initPyodide() {
  const { loadPyodide } = await import("pyodide");
  const py = await loadPyodide({ indexURL, env: getEnv(), packages: ["micropip"], args: dev ? [] : ["-O"] });
  py.globals.set("with_toast", withToast);
  py.globals.set("toast", toast);
  pyodideReady.set(true);
  return py;
}

export const getPyodide = cacheSingleton(withToast({ loading: "loading pyodide runtime" })(initPyodide));
