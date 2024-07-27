import workspace from "../../../python/workspace";
import { getPyodide, setupModule } from "./init";
import { cacheSingleton } from "$lib/utils/cache";

export const loadWorkspace = cacheSingleton(async () => {
  const py = await getPyodide();
  await setupModule(workspace, "workspace");
  return py;
});
