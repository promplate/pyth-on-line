<script lang="ts">
  import type { Link, Node } from "mdast";

  export let node: Node;

  $: link = node as Link;
</script>

<a href={link.url} title={link.title}>
  <slot />
</a>
