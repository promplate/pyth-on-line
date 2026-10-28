<script lang="ts">
  import type { Node } from "mdast";

  import WithCodeActions from "../reusable/WithCodeActions.svelte";
  import CodeBlock from "#lib/components/CodeBlock.svelte";

  const { node }: { node: Node } = $props();
</script>

<WithCodeActions {node}>
  {#snippet children(code)}
    <CodeBlock lang={code.lang ?? "text"} code={code.value} />
  {/snippet}
</WithCodeActions>
