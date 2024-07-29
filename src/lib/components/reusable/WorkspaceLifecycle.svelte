<script lang="ts">
  import type { WorkspaceAPI } from "$py/workspace/workspace";

  import getPy from "$lib/pyodide";
  import { onDestroy, onMount } from "svelte";

  export let sources: Record<string, string>;

  let workspace: WorkspaceAPI;

  onMount(async () => {
    const py = await getPy({ workspace: true });
    workspace = py.pyimport("workspace.WorkspaceAPI")(py.toPy(sources));
  });

  onDestroy(() => {
    workspace?.close();
    workspace?.destroy();
  });
</script>

<slot sync={workspace?.sync} save={workspace?.save} />
