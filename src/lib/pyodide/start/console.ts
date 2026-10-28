import console from "../../../python/console";
import { getPyodide, setupModule } from "./init";
import { pyodideState } from "#lib/pyodide/state.svelte.js";
import { cacheSingleton } from "#lib/utils/cache.js";

export const loadConsole = cacheSingleton(async () => {
  const py = await getPyodide();
  await setupModule(console, "console");
  pyodideState.ready = true;
  return py;
});
