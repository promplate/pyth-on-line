<script lang="ts">
  import type { ConsoleAPI } from "$py/console/console";
  import type { InlineCode, Node } from "mdast";

  import Tooltip from "../Tooltip.svelte";

  export let node: Node;
  export let inspect: typeof ConsoleAPI.prototype.inspect;

  let ref: HTMLElement;

  $: inlineCode = (node as InlineCode);

  let show = false;
  let inspection: { value: string; type: string };

  $: show && (inspection = inspect(inlineCode.value));
</script>

<!-- svelte-ignore a11y-mouse-events-have-key-events -->
<code class="p-4 -m-4" on:mouseover={() => show = true} on:mouseout={() => show = false} bind:this={ref}>{inlineCode.value}</code>

<Tooltip target={ref} show={show && inspection !== undefined}>
  <div class="max-w-lg flex flex-row items-center gap-1.5 overflow-x-hidden ws-nowrap rounded bg-neutral-8/80 p-1.5 pr-2 text-sm font-mono ring-(1.5 orange-3/80 inset) backdrop-blur -translate-y-2">
    <div class="rounded-sm bg-orange-3/10 px-1 py-0.5 text-xs text-orange-3 font-bold">{inspection?.type}</div>
    <div class="overflow-x-hidden text-ellipsis text-xs">{inspection?.value}</div>
  </div>
</Tooltip>
