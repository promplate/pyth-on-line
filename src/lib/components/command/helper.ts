import type { Cmd } from "./Item.svelte";

import { commands } from "./CmdK.svelte";
import { onDestroy, onMount } from "svelte";

export function registerCommandGroup(groupName: string, newCommands: { text: string; handler: (value: string) => any }[]) {
  onMount(() => {
    commands.update($commands => (
      {
        ...$commands,
        [groupName]: newCommands.map(
          ({ text, handler }) => ({ type: "cmd", text, callback: handler } as Cmd),
        ),
      }
    ));
  });
  onDestroy(() => {
    commands.update(({ [groupName]: _, ...rest }) => rest);
  });
}
