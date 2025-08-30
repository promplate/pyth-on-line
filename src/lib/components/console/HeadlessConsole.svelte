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

  import WithConsoleCommands from "./WithConsoleCommands.svelte";
  import getPy from "$lib/pyodide";
  import { needScroll, scrollToBottom } from "$lib/utils/scroll";
  import { onDestroy, onMount } from "svelte";

  let loading = $state(0);

  let {
    ready = $bindable(false),
    status = $bindable<Status>("complete"),
    log = $bindable<Item[]>([]),
    pyConsole = $bindable<ConsoleAPI>(),
    complete = $bindable<AutoComplete | undefined>(),
    container = $bindable<HTMLElement | undefined>(),
    push = $bindable(async (source: string, hidden = false) => {
      const res = pyConsole.push(source, hidden);
      if (res.status === "complete") {
        loading++;
        res.future.add_done_callback(() => loading--);
      }
      return res;
    }),
    children,
  } = $props();

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

  $effect.pre(() => {
    autoscroll = needScroll(container ?? document.documentElement, 500);
  });

  $effect(() => {
    autoscroll && scrollToBottom(container ?? document.documentElement);
  });

</script>

{@render children?.({ status, loading })}

<WithConsoleCommands {pyConsole} />
