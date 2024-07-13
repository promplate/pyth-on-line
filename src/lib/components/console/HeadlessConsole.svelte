<script context="module" lang="ts">
  export interface Item {
    type: "out" | "err" | "in" | "repr";
    text: string;
    incomplete?: boolean;
    is_traceback?: boolean;
  }

  export type AutoComplete = (source: string) => [string[], number];
  export type Status = "incomplete" | "syntax-error" | "complete";
</script>

<script lang="ts">
  import type { ConsoleAPI } from "$py/console/console";

  import getPy from "$lib/pyodide";
  import { onDestroy, onMount } from "svelte";

  export let ready = false;
  export let status: Status = "complete";
  export let log: Item[] = [];
  export let pyConsole: ConsoleAPI;
  export let complete: AutoComplete | undefined;

  let loading = 0;

  function syncLog() {
    log = pyConsole.get_items();
  }

  onMount(async () => {
    const py = await getPy({ console: true });
    pyConsole = (py.pyimport("console.console")).ConsoleAPI((syncLog));
    complete = pyConsole.complete;
    ready = true;
  });

  onDestroy(() => pyConsole?.destroy());

  export async function push(source: string) {
    loading++;
    const res = pyConsole.push(source);
    status = res.status;
    res.future.finally(() => loading--);
    return res;
  }
</script>

<slot {status} {loading} />
