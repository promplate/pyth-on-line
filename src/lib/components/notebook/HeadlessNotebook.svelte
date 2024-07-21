<script lang="ts">
  import type { NotebookAPI } from "$py/notebook/notebook";

  import getPy from "$lib/pyodide";
  import { onMount } from "svelte";

  let pyNotebook: NotebookAPI;

  onMount(async () => {
    const py = await getPy({ notebook: true });
    pyNotebook = py.pyimport("notebook.NotebookAPI")() as NotebookAPI;
  });
</script>

<slot {pyNotebook} />
