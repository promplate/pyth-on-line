<script lang="ts">
  import type { WorkspaceAPI } from "$py/workspace/workspace";
  import type { Snippet } from "svelte";

  import getPy from "$lib/pyodide";
  import { onMount } from "svelte";

  const { sources, children }: { sources: Record<string, string>; children: Snippet<[WorkspaceAPI | undefined]> } = $props();

  // Pyodide owns this handle; only its replacement should be reactive.
  let workspace = $state.raw<WorkspaceAPI>();

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

{@render children(workspace)}
