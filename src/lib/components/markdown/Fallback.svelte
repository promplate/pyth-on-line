<script context="module" lang="ts">
  import { toHtml } from "hast-util-to-html";
  import { toHast } from "mdast-util-to-hast";

  function stringify(root: any) {
    const hast = toHast(root);
    return toHtml(hast);
  }
</script>

<script lang="ts">
  import type { Node, Root } from "mdast";

  export let node: Node;

  $: root = node as Root;
</script>

{@html stringify(root)}
