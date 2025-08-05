import examples from "../../../python/examples";
import { getPyodide, setupModule } from "./init";
import { cacheSingleton } from "$lib/utils/cache";

export const loadExamples = cacheSingleton(async () => {
  const py = await getPyodide();
  await setupModule(examples, "examples");
  return py;
});