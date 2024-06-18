<script lang="ts">
  import Markdown from "./Markdown.svelte";
  import { draggable } from "@neodrag/svelte";
  import { explain } from "$lib/examples/explain";
  import { renderMarkdown } from "$lib/markdown";
  import { onMount } from "svelte";
  import { cubicIn, cubicOut } from "svelte/easing";
  import { scale } from "svelte/transition";

  interface Error { traceback: string; code: string }

  export let errorInfo: Error | undefined;

  let html = "";

  async function runExplain({ traceback, code }: Error) {
    let output = "";
    for await (const delta of explain(traceback, code)) {
      output += delta;
      html = await renderMarkdown(output, ["python"]);
    }
  }

  onMount(() => errorInfo && runExplain(errorInfo));

  let ref: HTMLDivElement;
</script>

<div class="mt-30vh h-full max-w-lg w-3/4 lg:max-w-xl">
  <div in:scale|global={{ start: 0.9, easing: cubicOut }} out:scale|global={{ start: 0.95, easing: cubicIn }} use:draggable={{ applyUserSelectHack: false, cancel: ref, bounds: { left: 20, top: 20, right: 20, bottom: 20 } }} class="flex flex-col cursor-grab rounded-lg bg-neutral-8/60 p-4 ring-1.3 ring-white/20 backdrop-blur-md xl:max-w-3xl" class:gap-3={html} class:sm:gap-4={html}>
    <div class="flex flex-row select-none items-center justify-between">
      <div class="flex flex-row items-center gap-1.5 rounded-md bg-emerald-3/10 px-1.5 py-1 text-emerald-3/80">
        <div class="i-majesticons-lightbulb-shine text-base text-emerald-3" />
        <div class="text-xs capitalize sm:text-sm">
          error explainer
        </div>
      </div>
      <button class="rounded-md p-1.5 text-white/80 transition-colors hover:(bg-red-3/10 text-red-3/80)" on:click={() => (errorInfo = undefined)}>
        <div class="i-material-symbols-close-rounded" />
      </button>
    </div>
    <div class="cursor-auto [&>article]:(<sm:text-xs lg:text-base)" bind:this={ref}>
      <Markdown {html} />
    </div>
  </div>
</div>
