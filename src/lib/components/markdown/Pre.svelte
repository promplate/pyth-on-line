<script lang="ts">
  import type { Node } from "mdast";

  import WithCodeActions from "../reusable/WithCodeActions.svelte";
  import CodeBlock from "$lib/components/CodeBlock.svelte";

  export let node: Node;
</script>

<WithCodeActions {node} let:code>
  <CodeBlock lang={code.lang ?? "text"} code={code.value} />
</WithCodeActions>
