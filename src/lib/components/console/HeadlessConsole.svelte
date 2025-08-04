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

  import WithConsoleCommands from "./WithConsoleCommands.svelte";
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

  export async function push(source: string, hidden = false) {
    const res = pyConsole.push(source, hidden);
    if (res.status === "complete") {
      loading++;
      res.future.add_done_callback(() => loading--);
    }
    return res;
  }
</script>

<slot {status} {loading} />

<WithConsoleCommands {pyConsole} />
