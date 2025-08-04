<script lang="ts">
  import type { Node, Root } from "mdast";

  import { toHtml } from "hast-util-to-html";
  import { toHast } from "mdast-util-to-hast";

  export let node: Node;

  $: root = node as Root;
</script>

{@html toHtml(toHast(root))}
