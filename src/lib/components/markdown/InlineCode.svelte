<script lang="ts">
  import type { ConsoleAPI, Inspection } from "$py/console/console";
  import type { InlineCode, Node } from "mdast";

  import Tooltip from "../Tooltip.svelte";

  export let node: Node;
  export let inspect: typeof ConsoleAPI.prototype.inspect;

  let ref: HTMLElement;

  $: inlineCode = (node as InlineCode);

  let show = false;
  let inspection: Inspection;

  $: show && (inspection = inspect(inlineCode.value));

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

<!-- svelte-ignore a11y-mouse-events-have-key-events -->
<code on:mouseover={() => show = true} on:mouseout={() => show = false} bind:this={ref}>{inlineCode.value}</code>

<Tooltip target={ref} show={show && inspection !== undefined}>
  <div class="{outerColor} max-w-lg flex flex-row items-center gap-1.5 overflow-x-hidden ws-nowrap rounded bg-neutral-8/80 p-1.5 pr-2 text-sm font-mono ring-(1.5 inset) backdrop-blur -translate-y-2">
    <div class="{classColor} rounded-sm px-1 py-0.5 text-xs font-bold">{inspection?.class}</div>
    <div class="{valueColor} overflow-x-hidden text-ellipsis text-xs">{inspection?.value}</div>
  </div>
</Tooltip>
