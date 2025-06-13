import reactivity from "../../../../packages/hmr/reactivity";
import notebook from "../../../python/notebook";
import { getPyodide, setupModule } from "./init";
import { cacheSingleton } from "$lib/utils/cache";

export const loadNotebook = cacheSingleton(async () => {
  const py = await getPyodide();
  await setupModule(reactivity, "reactivity");
  await setupModule(notebook, "notebook");
  return py;
});
