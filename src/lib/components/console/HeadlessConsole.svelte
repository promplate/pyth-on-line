<script context="module" lang="ts">
  import type { PythonError } from "pyodide/ffi";

  export interface Item {
    type: "out" | "err" | "in" | "repr";
    text: string;
    incomplete?: boolean;
    isTraceback?: boolean;
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

  onMount(async () => {
    const py = await getPy({ console: true });
    pyConsole = (py.pyimport("console.console")).ConsoleAPI();
    complete = pyConsole.complete;

    pyConsole.console.stdout_callback = text => pushLog({ type: "out", text });
    pyConsole.console.stderr_callback = text => pushLog({ type: "err", text });

    ready = true;
  });

  onDestroy(() => pyConsole?.destroy());

  export function pushLog(item: Item, behind?: Item) {
    if (!log.length)
      return void (log = [item]);

    const last = log.at(-1)!;

    if (last.type === item.type && (item.type === "out" || (item.type === "in" && last.incomplete) || (item.type === "err" && !last.isTraceback && !item.isTraceback))) {
      last.text += item.type === "in" ? `\n${item.text}` : item.text;
      last.incomplete = item.incomplete;
      log = [...log];
      return last;
    }
    else if (behind) {
      let index = log.findIndex(item => item === behind);
      if (log[index + 1]?.type === "out")
        index++;
      log = [...log.slice(0, index + 1), item, ...log.slice(index + 1)];
    }
    else {
      log = [...log, item];
    }
  }

  export async function push(source: string) {
    const res = pyConsole.push(source);
    status = res.status;

    let inputLog: Item = { type: "in", text: source, incomplete: status === "incomplete" };
    inputLog = pushLog(inputLog) ?? inputLog;

    if (status === "syntax-error") {
      pushLog({ type: "err", text: `Traceback (most recent call last):\n${res.formatted_error}`, isTraceback: true }, inputLog);
    }
    else if (status === "complete") {
      loading++;
      try {
        const text = await res.get_repr();
        if (text !== undefined) {
          pushLog({ type: "repr", text }, inputLog);
        }
      }
      catch (e) {
        const err = (res.formatted_error ?? (e as PythonError).message);
        pushLog({ type: "err", text: err.slice(err.lastIndexOf("Traceback (most recent call last):")), isTraceback: true }, inputLog);
      }
      finally {
        loading--;
      }
    }
  }
</script>

<slot {status} {loading} />
