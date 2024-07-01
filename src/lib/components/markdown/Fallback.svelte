<script context="module">
  import rehypeStringify from "rehype-stringify";
  import remarkRehype from "remark-rehype";
  import { unified } from "unified";

  const processor = unified().use(remarkRehype).use(rehypeStringify);
</script>

<script lang="ts">
  import type { Node, Root } from "mdast";

  export let node: Node;

  $: root = node as Root;
</script>

{@html String(processor.stringify(processor.runSync(root)))}
