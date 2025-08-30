<script lang="ts">
  import type { Link, Node } from "mdast";

  interface Props {
    node: Node;
    children?: import("svelte").Snippet;
  }

  const { node, children }: Props = $props();

  const link = $derived(node as Link);
</script>

<a href={link.url} title={link.title}>
  {@render children?.()}
</a>
