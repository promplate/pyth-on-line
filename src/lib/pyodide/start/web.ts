import web from "../../../python/web";
import { getPyodide, setupModule } from "./init";
import { cacheSingleton } from "$lib/utils/cache";

export const loadWeb = cacheSingleton(async () => {
  const py = await getPyodide();
  await setupModule(web, "web");
  return py;
});
