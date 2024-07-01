import { getPy } from ".";
import chat from "../../python/chat";
import { getSetupModule } from "./init";
import { cacheSingleton } from "$lib/utils/cache";

export const loadChat = cacheSingleton(async () => {
  const py = await getPy();
  const setupModule = await getSetupModule();
  setupModule(py.toPy(chat), "chat");
  await py.pyimport("chat").asynchronous_bootstrap() as Promise<void>;
});

export async function* explain(traceback: string, code: string): AsyncGenerator<string> {
  const py = await getPy();
  await loadChat();
  const explain = py.pyimport("chat.explain").explain;
  yield * explain(traceback, code);
}
