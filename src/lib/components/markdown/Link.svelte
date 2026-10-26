<script lang="ts">
  import type { Link, Node } from "mdast";
  import type { Snippet } from "svelte";

  const { node, children }: { node: Node; children?: Snippet } = $props();

  const link = $derived(node as Link);
</script>

<a href={link.url} title={link.title}>
  {@render children?.()}
</a>
