<script lang="ts">
  import type { NotebookAPI } from "$py/notebook/notebook";

  import getPy from "$lib/pyodide";
  import { onDestroy, onMount } from "svelte";

  interface Props {
    children?: import("svelte").Snippet<[any]>;
  }

  const { children }: Props = $props();

  let pyNotebook: NotebookAPI = $state();

  onMount(async () => {
    const py = await getPy({ notebook: true });
    pyNotebook = py.pyimport("notebook.NotebookAPI")() as NotebookAPI;
  });

  onDestroy(() => pyNotebook?.destroy());
</script>

{@render children?.({ pyNotebook })}
