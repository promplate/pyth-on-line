<script lang="ts">
  import type { NotebookAPI } from "$py/notebook/notebook";

  import getPy from "$lib/pyodide";
  import { patchSource } from "$lib/utils/formatSource";
  import { onMount } from "svelte";

  let pyNotebook: NotebookAPI;

  onMount(async () => {
    const py = await getPy({ notebook: true });
    pyNotebook = py.pyimport("notebook.NotebookAPI")() as NotebookAPI;
  });

  async function pushBlock(source: string) {
    return await pyNotebook.run(patchSource(source));
  }
</script>

<slot {pyNotebook} {pushBlock} />
