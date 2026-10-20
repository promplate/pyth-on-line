import type { Cmd } from "./Item.svelte";

import { commandMenu } from "./state.svelte";
import { onMount } from "svelte";

export interface Command {
  text: string;
  handler: (value: string) => any;
}

// Multiple live components may share a group name; keep the latest mounted owner visible.
const registrations = new Map<string, Cmd[][]>();

export function registerCommandGroup(groupName: string, newCommands: Command[]) {
  onMount(() => {
    const group = newCommands.map(({ text, handler }) => ({ type: "cmd", text, callback: handler } as Cmd));
    const stack = registrations.get(groupName) ?? [];
    stack.push(group);
    registrations.set(groupName, stack);
    commandMenu.commands = { ...commandMenu.commands, [groupName]: group };
    return () => {
      stack.splice(stack.indexOf(group), 1);
      if (!stack.length)
        registrations.delete(groupName);
      if (commandMenu.commands[groupName] !== group)
        return;
      const previous = stack.at(-1);
      if (previous) {
        commandMenu.commands = { ...commandMenu.commands, [groupName]: previous };
        return;
      }
      const { [groupName]: _, ...rest } = commandMenu.commands;
      commandMenu.commands = rest;
    };
  });
}
