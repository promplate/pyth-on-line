<script lang="ts">
  import type { Code, Node } from "mdast";

  import CodeBlock from "$lib/components/CodeBlock.svelte";

  export let node: Node;

  $: code = node as Code;
</script>

<CodeBlock lang={code.lang ?? "text"} code={code.value} />
