<script lang="ts">
  import type { WorkspaceAPI } from "$py/workspace/workspace";

  import getPy from "$lib/pyodide";
  import { onMount } from "svelte";

  export let sources: Record<string, string>;

  let workspace: WorkspaceAPI;

  onMount(() => {
    let disposed = false;

    // Pyodide is shared; skip late resource creation without cancelling its initialization.
    getPy({ workspace: true }).then((py) => {
      if (disposed)
        return;
      workspace = py.pyimport("workspace.WorkspaceAPI")(py.toPy(sources));
    });

    return () => {
      disposed = true;
      workspace?.close();
      workspace?.destroy();
    };
  });
</script>

<slot sync={workspace?.sync} save={workspace?.save} />
