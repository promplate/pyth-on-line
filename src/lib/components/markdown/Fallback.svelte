<script lang="ts">
  import type { Node, Root } from "mdast";

  import { toHtml } from "hast-util-to-html";
  import { toHast } from "mdast-util-to-hast";

  const { node }: { node: Node } = $props();

  const root = $derived(node as Root);
</script>

{@html toHtml(toHast(root))}
