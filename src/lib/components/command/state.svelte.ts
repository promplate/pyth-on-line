import type { Item } from "./Item.svelte";

// This singleton belongs to the browser UI; register groups in onMount, never during SSR.
class CommandMenu {
  show = $state(false);
  commands = $state.raw<Record<string, Item[]>>({});
  getItems = $state.raw<((input: string) => Item[])>();
  prefixes = $state.raw<string[]>([]);
  input = $state("");
  placeholder = $state("");
}

export const commandMenu = new CommandMenu();
