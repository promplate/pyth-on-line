<script lang="ts">
  import type { ConsoleAPI } from "$py/console/console";

  import Markdown from "./chat/Markdown.svelte";
  import WithTooltip from "./reusable/WithTooltip.svelte";
  import { draggable } from "@neodrag/svelte";
  import { explain } from "$lib/pyodide/api/explain";
  import { onMount } from "svelte";
  import { cubicIn, cubicOut } from "svelte/easing";
  import { scale } from "svelte/transition";

  interface ErrorInfo { traceback: string; code: string }

  export let errorInfo: ErrorInfo | undefined;
  export let pushBlock: (source: string) => any;
  export let pyConsole: ConsoleAPI;
  export let close: () => any;

  let output = "";
  let error: Error | undefined;

  async function runExplain({ traceback, code }: ErrorInfo) {
    try {
      for await (const delta of explain(traceback, code))
        output += delta;
    }
    catch (e) {
      error = e as Error;
    }
  }

  function invoke() {
    if (errorInfo) {
      output = "";
      error = undefined;
      runExplain(errorInfo);
    }
  }

  onMount(invoke);

  let ref: HTMLDivElement;
</script>

<div class="mt-10 h-full max-w-[calc(100vw-40px)] w-full sm:mt-30vh lg:max-w-xl sm:max-w-lg sm:w-3/4">
  <div in:scale|global={{ start: 0.9, easing: cubicOut }} out:scale|global={{ start: 0.95, easing: cubicIn }} use:draggable={{ applyUserSelectHack: false, cancel: ref, bounds: { left: 20, top: 20, right: 20, bottom: 20 } }} class="max-h-[calc(100vh-40px)] flex flex-col cursor-grab gap-3 rounded bg-neutral-8/60 p-3 ring-0.9 ring-white/20 backdrop-blur-md xl:max-w-3xl sm:gap-4 lg:p-4 sm:p-3.5 lg:ring-1.3 sm:ring-1.1" class:!pb-0={output}>
    <div class="flex flex-row select-none items-center justify-between">
      <div class="flex flex-row items-center gap-1.5 rounded bg-emerald-3/10 px-1.5 py-1 text-emerald-3/80">
        <div class="i-majesticons-lightbulb-shine text-base text-emerald-3" />
        <div class="text-xs capitalize sm:text-sm">
          报错解释与修复
        </div>
      </div>
      <div class="flex flex-row [&>button:active]:scale-90 [&>button]:(rounded p-1.5 text-white/80 transition-colors)">
        <WithTooltip tips="重新生成" let:builder>
          <button class="hover:(bg-cyan-3/10 text-cyan-3/80)" on:click={invoke} {...builder} use:builder.action>
            <div class="i-mingcute-refresh-2-fill" />
          </button>
        </WithTooltip>
        <WithTooltip tips="关闭" let:builder>
          <button class="hover:(bg-red-3/10 text-red-3/80)" on:click={close} {...builder} use:builder.action>
            <div class="i-mingcute-close-fill" />
          </button>
        </WithTooltip>
      </div>
    </div>
    <div class="contents cursor-auto" bind:this={ref}>
      {#if error}
        <div class="overflow-x-scroll overflow-x-scroll rounded bg-orange-3/5 text-xs text-orange-3">
          <pre class="px-2.5 py-2 font-mono">{error.message}</pre>
        </div>
      {/if}
      {#if output}
        <div class="overflow-y-scroll pb-2.5 lg:pb-3.5 sm:pb-3 [&>article]:(<sm:text-xs lg:text-base)">
          <Markdown text={output} runCode={pushBlock} inspect={pyConsole.inspect} />
        </div>
      {/if}
    </div>
  </div>
</div>
