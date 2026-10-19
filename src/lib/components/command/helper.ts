import type { Cmd } from "./Item.svelte";

import { commandMenu } from "./state.svelte";
import { onMount } from "svelte";

export interface Command {
  text: string;
  handler: (value: string) => any;
}

export function registerCommandGroup(groupName: string, newCommands: Command[]) {
  onMount(() => {
    const group = newCommands.map(({ text, handler }) => ({ type: "cmd", text, callback: handler } as Cmd));
    commandMenu.commands = { ...commandMenu.commands, [groupName]: group };
    return () => {
      if (commandMenu.commands[groupName] !== group)
        return;
      const { [groupName]: _, ...rest } = commandMenu.commands;
      commandMenu.commands = rest;
    };
  });
}
