<script lang="ts">
  import type { Item, NotebookAPI } from "$py/notebook/notebook";
  import type { Code, Node } from "mdast";

  import WithCodeActions from "../reusable/WithCodeActions.svelte";
  import CodeBlock from "$lib/components/CodeBlock.svelte";
  import { patchSource } from "$lib/utils/formatSource";

  interface Props {
    node: Node;
    pyNotebook: NotebookAPI;
    heuristics?: boolean;
  }

  const { node, pyNotebook, heuristics = false }: Props = $props();

  let items: Item[] = $state([]);

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

  const valid = $derived(isPython(pyNotebook, (node as Code).value));
</script>

<WithCodeActions {node} {run} runnable={valid}>
  {#snippet children({ code })}
    <CodeBlock lang={code.lang ?? valid ? "python" : "text"} code={code.value} {items} />
  {/snippet}
</WithCodeActions>
