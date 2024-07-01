import { getPyodide } from "./start/init";

export default async function getPy(feature: { console?: boolean; chat?: boolean } = {}) {
  const { console = false, chat = false } = feature;

  if (console) {
    const { loadConsole } = await import("./start/console");
    await loadConsole();
  }
  if (chat) {
    const { loadChat } = await import("./start/chat");
    await loadChat();
  }

  return await getPyodide();
}
