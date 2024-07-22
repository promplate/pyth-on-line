<script lang="ts">
  import type { Item, NotebookAPI } from "$py/notebook/notebook";
  import type { Node } from "mdast";

  import WithCodeActions from "../reusable/WithCodeActions.svelte";
  import CodeBlock from "$lib/components/CodeBlock.svelte";
  import { patchSource } from "$lib/utils/formatSource";

  export let node: Node;
  export let pyNotebook: NotebookAPI;
  export let heuristics = false;

  let items: Item[] = [];

  async function run(source: string) {
    pyNotebook.run(patchSource(source), newItems => items = newItems);
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

</script>

<WithCodeActions {node} {run} let:code>
  <CodeBlock lang={code.lang ?? isPython(pyNotebook, code.value) ? "python" : "text"} code={code.value} {items} />
</WithCodeActions>
