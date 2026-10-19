<script lang="ts">
  import type { Item, NotebookAPI } from "$py/notebook/notebook";
  import type { Code, Node } from "mdast";

  import WithCodeActions from "../reusable/WithCodeActions.svelte";
  import CodeBlock from "$lib/components/CodeBlock.svelte";
  import { patchSource } from "$lib/utils/formatSource";

  const { node, pyNotebook, heuristics = false }: { node: Node; pyNotebook?: NotebookAPI; heuristics?: boolean } = $props();

  let items = $state.raw<Item[]>([]);

  const code = $derived(node as Code);

  function sync(newItems: Item[]) {
    items = newItems;
  }

  async function run(source: string) {
    const notebook = pyNotebook;
    if (!notebook)
      return;
    if (source.startsWith(">>>")) {
      notebook.run(patchSource(source), sync, true);
    }
    else {
      notebook.run(source, sync);
    }
  }

  function isPython(pyNotebook: NotebookAPI | undefined, source: string) {
    if (!heuristics)
      return false;
    if (source.startsWith(">>>"))
      return true;
    if (pyNotebook?.is_python(source))
      return true;
    return false;
  }

  const valid = $derived(isPython(pyNotebook, code.value));

  const lang = $derived.by(() => {
    if (code.lang)
      return code.lang;
    try {
      JSON.parse(code.value);
      return "json";
    }
    catch {
      return valid ? "python" : "text";
    }
  });
</script>

<WithCodeActions {node} run={pyNotebook ? run : null} runnable={valid}>
  {#snippet children(code)}
    <CodeBlock {lang} code={code.value} {items} />
  {/snippet}
</WithCodeActions>
