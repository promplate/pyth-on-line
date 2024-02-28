import { pyodideReady } from "../stores";
import * as env from "$env/static/public";
import { cacheSingleton } from "$lib/utils/cache";
import { withToast } from "$lib/utils/toast";
import { toast } from "svelte-sonner";

const indexURL = typeof window === "undefined" ? undefined : (process.env.NODE_ENV === "production" && "/pyodide/") || "https://promplate.dev/pyodide/";

async function initPyodide() {
  const { loadPyodide } = await import("pyodide");
  return await loadPyodide({ indexURL, env: { ...env }, packages: ["micropip", "typing-extensions"] });
}

async function initPy() {
  const [py, { AsyncClient }, version, { default: initCode }] = await Promise.all([
    initPyodide(),
    import("./translate"),
    import("openai/version"),
    import("./init.py?raw"),
  ]);
  const info = toast.loading("installing extra python dependencies");

  py.registerJsModule("openai", { AsyncClient, Client: () => null, version, __all__: [] });
  py.registerJsModule("httpx", { AsyncClient: () => null, Client: () => null });

  await py.runPythonAsync(initCode);

  toast.dismiss(info);

  pyodideReady.set(true);

  return py;
}

export const getPy = cacheSingleton(withToast(initPy, { loading: "preparing pyodide runtime", success: `successfully initialized pyodide runtime` }));

export async function initConsole() {
  const [py, { default: initConsoleCode }] = await Promise.all([getPy(), import("./console.py?raw")]);
  await py.runPythonAsync(initConsoleCode);
}
