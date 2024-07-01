<script lang="ts">
  import type { InlineCode, Node } from "mdast";

  export let node: Node;

  $: inlineCode = (node as InlineCode);
</script>

<code>{inlineCode.value}</code>
