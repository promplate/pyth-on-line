<script lang="ts">
  import type { NotebookAPI } from "$py/notebook/notebook";
  import type { Node } from "mdast";

  import WithCodeActions from "../reusable/WithCodeActions.svelte";
  import CodeBlock from "$lib/components/CodeBlock.svelte";

  export let node: Node;
  // eslint-disable-next-line no-undef-init
  export let pyNotebook: NotebookAPI | undefined = undefined;
</script>

<WithCodeActions {node} let:code>
  <CodeBlock
    lang={code.lang ?? "text"}
    code={code.value}
    {pyNotebook}
    enableInspection={code.lang === "python" && !!pyNotebook}
  />
</WithCodeActions>
