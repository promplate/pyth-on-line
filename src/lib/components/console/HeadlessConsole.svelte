<script module lang="ts">
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
  import type { Snippet } from "svelte";

  import WithConsoleCommands from "./WithConsoleCommands.svelte";
  import getPy from "$lib/pyodide";
  import { needScroll, scrollToBottom } from "$lib/utils/scroll";
  import { onMount, tick } from "svelte";

  let { ready = $bindable(false), status = $bindable<Status>("complete"), log = $bindable<Item[]>([]), pyConsole = $bindable<ConsoleAPI>(), complete = $bindable<AutoComplete>(), container, children }: {
    ready?: boolean;
    status?: Status;
    log?: Item[];
    pyConsole?: ConsoleAPI;
    complete?: AutoComplete;
    container?: HTMLElement;
    children: Snippet<[{ status: Status; loading: number }]>;
  } = $props();

  let loading = $state(0);
  let disposed = false;

  function syncLog() {
    if (disposed || !pyConsole)
      return;
    log = pyConsole.get_items();
    status = pyConsole.incomplete ? "incomplete" : "complete";
  }

  onMount(() => {
    getPy({ console: true }).then((py) => {
      if (disposed)
        return;
      pyConsole = (py.pyimport("console.console")).ConsoleAPI((syncLog)) as ConsoleAPI;
      complete = pyConsole.complete;
      ready = true;
    });

    return () => {
      disposed = true;
      pyConsole?.close();
      pyConsole?.destroy();
    };
  });

  $effect.pre(() => {
    // Measure the old DOM before output or prompt state changes are rendered.
    void [log, status, loading, ready];
    const target = container ?? document.documentElement;
    if (!needScroll(target, 500))
      return;
    tick().then(() => {
      if (!disposed && target === (container ?? document.documentElement))
        scrollToBottom(target);
    });
  });

  export async function push(source: string, hidden = false) {
    if (disposed || !pyConsole)
      throw new Error("Console is not ready");
    const res = pyConsole.push(source, hidden);
    if (res.status === "complete") {
      loading++;
      res.future.add_done_callback(() => {
        if (!disposed)
          loading--;
      });
    }
    return res;
  }
</script>

{@render children({ status, loading })}

<WithConsoleCommands {pyConsole} />
