import chat from "../../../python/chat";
import { getPyodide, setupModule } from "./init";
import { cacheSingleton } from "$lib/utils/cache";
import { OpenAI } from "openai";
import * as version from "openai/version";

export const loadChat = cacheSingleton(async () => {
  const py = await getPyodide();
  py.registerJsModule("openai", { OpenAI, version, __all__: [] });
  await setupModule(chat, "chat");
  await py.pyimport("chat.install_requirements");
});
