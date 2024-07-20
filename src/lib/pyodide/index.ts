import { getPyodide } from "./start/init";

export default async function getPy(feature: { console?: boolean; chat?: boolean; notebook?: boolean } = {}) {
  const { console = false, notebook = false, chat = false } = feature;

  if (console) {
    const { loadConsole } = await import("./start/console");
    await loadConsole();
  }
  if (notebook) {
    const { loadNotebook } = await import("./start/notebook");
    await loadNotebook();
  }
  if (chat) {
    const { loadChat } = await import("./start/chat");
    await loadChat();
  }

  return await getPyodide();
}
