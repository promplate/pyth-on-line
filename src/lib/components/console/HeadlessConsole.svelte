<script context="module" lang="ts">
  export interface Item {
    type: "out" | "err" | "in" | "repr";
    text: string;
    incomplete?: boolean;
    is_traceback?: boolean;
  }

  export type AutoComplete = (source: string) => [string[], number];
  export type Status = "incomplete" | "complete";
</script>

<script lang="ts">
  import type { ConsoleAPI } from "$py/console/console";

  import { registerCommands } from "../command/helper";
  import getPy from "$lib/pyodide";
  import { needScroll, scrollToBottom } from "$lib/utils/scroll";
  import { afterUpdate, beforeUpdate, onDestroy, onMount } from "svelte";

  export let ready = false;
  export let status: Status = "complete";
  export let log: Item[] = [];
  export let pyConsole: ConsoleAPI;
  export let complete: AutoComplete | undefined;
  export let container: HTMLElement | undefined;

  let loading = 0;

  function syncLog() {
    log = pyConsole.get_items();
    status = pyConsole.incomplete ? "incomplete" : "complete";
  }

  onMount(async () => {
    const py = await getPy({ console: true });
    pyConsole = (py.pyimport("console.console")).ConsoleAPI((syncLog));
    complete = pyConsole.complete;
    ready = true;
  });

  onDestroy(() => {
    pyConsole?.close();
    pyConsole?.destroy();
  });

  let autoscroll = false;

  beforeUpdate(() => {
    autoscroll = needScroll(container ?? document.documentElement, 500);
  });

  afterUpdate(() => {
    autoscroll && scrollToBottom(container ?? document.documentElement);
  });

  export async function push(source: string) {
    const res = pyConsole.push(source);
    if (res.status === "complete") {
      loading++;
      res.future.add_done_callback(() => loading--);
    }
    return res;
  }

  registerCommands("Console", [
    {
      text: "Clear Console",
      handler() {
        pyConsole.clear();
      },
    },
    {
      text: "Install Packages",
      async handler() {
        // eslint-disable-next-line no-alert
        const packages = prompt()?.split(" ").filter(Boolean);
        if (packages?.length) {
          const py = await getPy();
          await py.pyimport("micropip.install")(packages);
        }
      },
    },
  ]);
</script>

<slot {status} {loading} />
