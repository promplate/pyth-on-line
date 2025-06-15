<script lang="ts">
  import type { ConsoleAPI, Inspection } from "$py/console/console";
  import type { NotebookAPI } from "$py/notebook/notebook";
  import type { InlineCode, Node } from "mdast";

  import Tooltip from "../Tooltip.svelte";
  import { onDestroy } from "svelte";

  export let node: Node;
  export let inspect: typeof ConsoleAPI.prototype.inspect | null = null;
  export let watch: typeof NotebookAPI.prototype.watch | null = null;

  let ref: HTMLElement;

  $: inlineCode = (node as InlineCode);

  let show = false;
  let inspection: Inspection;

  $: show && inspect && (inspection = inspect(inlineCode.value));

  const callbacks: (() => void)[] = [];

  $: show && watch && !callbacks.length && callbacks.push(watch(inlineCode.value, result => (inspection = result)));

  function stopWatching() {
    while (callbacks.length) callbacks.pop()!();
  }

  onDestroy(stopWatching);

  let outerColor: string;
  let classColor: string;
  let valueColor: string;

  $: {
    switch (inspection?.type) {
      case "class": {
        outerColor = "ring-orange-3/80";
        classColor = "bg-orange-3/10 text-orange-3";
        valueColor = "text-orange-50";
        break;
      }
      case "exception": {
        outerColor = "ring-rose-3/80";
        classColor = "bg-rose-3/10 text-rose-3";
        valueColor = "text-rose-50";
        break;
      }
      default: {
        outerColor = "ring-blue-3/80";
        classColor = "bg-blue-3/10 text-blue-3";
        valueColor = "text-blue-50";
      }
    }
  }
</script>

{#if inspect || watch}
  <Tooltip target={ref} show={show && inspection !== undefined} onHide={stopWatching}>
    <div class="{outerColor} max-w-lg flex flex-row items-center gap-1.5 overflow-x-hidden ws-nowrap rounded bg-neutral-8/80 p-1.5 pr-2 text-sm text-xs font-mono ring-(1.5 inset) backdrop-blur -translate-y-0.4em <lg:(text-2.75 ring-1.3) <sm:(text-2.5 ring-1.1)">
      <div class="{classColor} rounded-sm px-1 py-0.5 font-bold <lg:(px-0.75 py-0.25) <sm:(px-0.5 py-0)">{inspection?.class}</div>
      <div class="{valueColor} overflow-x-hidden text-ellipsis">{inspection?.value}</div>
    </div>
  </Tooltip>

  <code on:mouseenter={() => show = true} on:mouseleave={() => [(show = false), stopWatching()]} bind:this={ref}>{inlineCode.value}</code>
{:else}
  <code>{inlineCode.value}</code>
{/if}
