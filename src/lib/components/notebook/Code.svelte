<script lang="ts">
  import type { Item, NotebookAPI } from "$py/notebook/notebook";
  import type { Code, Node } from "mdast";

  import WithCodeActions from "../reusable/WithCodeActions.svelte";
  import CodeBlock from "$lib/components/CodeBlock.svelte";
  import { patchSource } from "$lib/utils/formatSource";

  export let node: Node;
  export let pyNotebook: NotebookAPI;
  export let heuristics = false;

  let items: Item[] = [];

  function sync(newItems: Item[]) {
    items = newItems;
  }

  async function run(source: string) {
    if (source.startsWith(">>>")) {
      pyNotebook.run(patchSource(source), sync, true);
    }
    else {
      pyNotebook.run(source, sync);
    }
  }

  function isPython(pyNotebook: NotebookAPI, source: string) {
    if (!heuristics)
      return false;
    if (source.startsWith(">>>"))
      return true;
    if (pyNotebook?.is_python(source))
      return true;
    return false;
  }

  $: valid = isPython(pyNotebook, (node as Code).value);
</script>

<WithCodeActions {node} {run} runnable={valid} let:code>
  <CodeBlock lang={code.lang ?? valid ? "python" : "text"} code={code.value} {items} />
</WithCodeActions>
