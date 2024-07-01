import console from "../../../python/console";
import { getPyodide, setupModule } from "./init";
import { pyodideReady } from "$lib/stores";
import { cacheSingleton } from "$lib/utils/cache";

export const loadConsole = cacheSingleton(async () => {
  const py = await getPyodide();
  await setupModule(console, "console");
  pyodideReady.set(true);
  return py;
});
