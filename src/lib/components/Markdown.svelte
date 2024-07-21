<script context="module">
  import "../md.css";

  import remarkParse from "remark-parse";
  import { unified } from "unified";

  const processor = unified().use(remarkParse);
</script>

<script lang="ts">
  import type { ConsoleAPI } from "$py/console/console";
  import type { RunResult } from "$py/notebook/notebook";

  import Node from "./markdown/Node.svelte";

  export let text: string;
  export let runCode: (source: string) => Promise<RunResult> | undefined;
  export let inspect: typeof ConsoleAPI.prototype.inspect;

  $: node = processor.parse(text);
</script>

<article class="max-w-full text-sm text-neutral-2 font-sans prose [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
  <Node {node} {runCode} {inspect} />
</article>
