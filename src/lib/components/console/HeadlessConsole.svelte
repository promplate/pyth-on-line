<script context="module" lang="ts">
  import type { PyProxy, PythonError } from "pyodide/ffi";

  export interface Item {
    type: "out" | "err" | "in" | "repr";
    text: string;
    incomplete?: boolean;
  }

  export type AutoComplete = (source: string) => [string[], number];
  export type Status = "incomplete" | "syntax-error" | "complete";
</script>

<script lang="ts">
  import type { Console } from "$py/app/console";

  import { getPy } from "$lib/pyodide";
  import { onMount } from "svelte";

  export let ready = false;
  export let status: Status = "complete";
  export let log: Item[] = [];
  export let pyConsole: Console;
  export let complete: AutoComplete | undefined;

  let loading = 0;

  onMount(async () => {
    const py = await getPy();
    const consoleModule: PyProxy = py.globals.get("consoleModule");
    pyConsole = consoleModule.Console();
    consoleModule.destroy();
    complete = pyConsole.complete;

    pyConsole.console.stdout_callback = text => pushLog({ type: "out", text });
    pyConsole.console.stderr_callback = text => pushLog({ type: "err", text });

    ready = true;
  });

  export function pushLog(item: Item, behind?: Item) {
    if (!log.length)
      return void (log = [item]);

    const last = log.at(-1)!;

    if (last.type === item.type && (item.type === "out" || (item.type === "in" && last.incomplete))) {
      last.text += item.type === "in" ? `\n${item.text}` : item.text;
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
      pushLog({ type: "err", text: `Traceback (most recent call last):\n${res.formatted_error}` }, inputLog);
    }
    else if (status === "complete") {
      loading++;
      try {
        const [proxy, repr] = await res.get_value_and_repl();
        if (proxy != null) {
          pushLog({ type: "repr", text: repr }, inputLog);
          proxy.destroy && proxy.destroy();
        }
      }
      catch (e) {
        const err = (res.formatted_error ?? (e as PythonError).message);
        pushLog({ type: "err", text: err.slice(err.lastIndexOf("Traceback (most recent call last):")) }, inputLog);
      }
      finally {
        res.destroy();
        loading--;
      }
    }
  }
</script>

<slot {status} {loading} />
