<script lang="ts">
  import type { Item, NotebookAPI } from "$py/notebook/notebook";
  import type { Node } from "mdast";

  import WithCodeActions from "../reusable/WithCodeActions.svelte";
  import CodeBlock from "$lib/components/CodeBlock.svelte";
  import { patchSource } from "$lib/utils/formatSource";

  export let node: Node;
  export let pyNotebook: NotebookAPI;

  let items: Item[] = [];

  async function run(source: string) {
    pyNotebook.run(patchSource(source), newItems => items = newItems);
  }

</script>

<WithCodeActions {node} {run} let:code>
  <CodeBlock lang={code.lang ?? "text"} code={code.value} {items} />
</WithCodeActions>
