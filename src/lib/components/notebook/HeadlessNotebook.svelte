<script lang="ts">
  import type { NotebookAPI } from "#py/notebook/notebook.js";
  import type { Snippet } from "svelte";

  import getPy from "#lib/pyodide/index.js";
  import { onMount } from "svelte";

  const { children }: { children: Snippet<[NotebookAPI | undefined]> } = $props();

  // Pyodide owns this handle, so only track its replacement, not its internals.
  let pyNotebook = $state.raw<NotebookAPI>();

  onMount(() => {
    let disposed = false;

    getPy({ notebook: true }).then((py) => {
      if (disposed)
        return;
      pyNotebook = py.pyimport("notebook.NotebookAPI")() as NotebookAPI;
    });

    return () => {
      disposed = true;
      pyNotebook?.destroy();
    };
  });
</script>

{@render children(pyNotebook)}
