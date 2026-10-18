<script lang="ts">
  import type { NotebookAPI } from "$py/notebook/notebook";

  import getPy from "$lib/pyodide";
  import { onMount } from "svelte";

  let pyNotebook: NotebookAPI;

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

<slot {pyNotebook} />
