<script lang="ts">
  import type { ConsoleAPI } from "$py/console/console";
  import type { InlineCode, Node } from "mdast";

  export let node: Node;
  export let inspect: typeof ConsoleAPI.prototype.inspect;

  $: inlineCode = (node as InlineCode);
</script>

<!-- svelte-ignore a11y-mouse-events-have-key-events -->
<code on:mouseover={() => console.log(inspect(inlineCode.value))}>{inlineCode.value}</code>
