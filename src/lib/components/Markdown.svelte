<script context="module">
  import "../md.css";

  import remarkParse from "remark-parse";
  import { unified } from "unified";

  const processor = unified().use(remarkParse);
</script>

<script lang="ts">
  import Node from "./markdown/Node.svelte";

  export let text: string;

  $: node = processor.parse(text);
</script>

<article class="min-w-full text-sm text-neutral-2 font-sans prose [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
  <Node {node} />
</article>
