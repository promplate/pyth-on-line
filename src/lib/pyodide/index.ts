import { getPyodide } from "./start/init";

export default async function getPy(feature: { console?: boolean; chat?: boolean; notebook?: boolean; web?: boolean; workspace?: boolean } = {}) {
  const { console = false, chat = false, notebook = false, web = false, workspace = false } = feature;

  if (console) {
    const { loadConsole } = await import("./start/console");
    await loadConsole();
  }
  if (notebook) {
    const { loadNotebook } = await import("./start/notebook");
    await loadNotebook();
  }
  if (web) {
    const { loadWeb } = await import("./start/web");
    await loadWeb();
  }
  if (chat) {
    const { loadChat } = await import("./start/chat");
    await loadChat();
  }
  if (workspace) {
    const { loadWorkspace } = await import("./start/workspace");
    await loadWorkspace();
  }

  return await getPyodide();
}
