<script lang="ts">
  import type { Cmd } from "../command/Item.svelte";
  import type { ConsoleAPI } from "$py/console/console";

  import { registerCommandGroup } from "../command/helper";
  import { commandMenu } from "../command/state.svelte";
  import getPy from "$lib/pyodide";
  import { onMount, tick } from "svelte";

  const { pyConsole }: { pyConsole?: ConsoleAPI } = $props();

  const installTitle = "Install Packages";
  let frame: number | undefined;
  let disposed = false;

  // Selection closes the menu in finally; reopen it on the next frame.
  function openMenu() {
    if (disposed)
      return;
    if (frame !== undefined)
      cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => {
      frame = undefined;
      commandMenu.show = true;
    });
  }

  const installItems = (input: string): Cmd[] => [{
    async callback() {
      resetInstall();
      await tick();

      const packages = input.split(" ").filter(Boolean);
      if (packages.length) {
        const py = await getPy();
        py.pyimport("micropip.install")(packages);
      }
      else {
        openMenu();
      }
    },
    type: "cmd",
    text: input ? `pip install ${input}` : "(cancel)",
    alwaysRender: true,
  }];

  function resetInstall() {
    if (commandMenu.getItems !== installItems)
      return;
    commandMenu.getItems = undefined;
    commandMenu.prefixes = [];
    commandMenu.placeholder = "";
  }

  onMount(() => () => {
    disposed = true;
    if (frame !== undefined)
      cancelAnimationFrame(frame);
    if (commandMenu.getItems === installItems) {
      resetInstall();
      commandMenu.input = "";
      commandMenu.show = false;
    }
  });

  registerCommandGroup("Console", [
    {
      text: installTitle,
      handler() {
        commandMenu.prefixes = [installTitle];
        commandMenu.placeholder = "<package1> <package2> ...";
        commandMenu.getItems = installItems;
        openMenu();
      },
    },
    {
      text: "Clear Console",
      handler() {
        pyConsole?.clear();
      },
    },
  ]);
</script>
