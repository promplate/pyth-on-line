<script lang="ts">
  import type { WorkspaceAPI } from "$py/workspace/workspace";

  import getPy from "$lib/pyodide";
  import { onDestroy, onMount } from "svelte";

  interface Props {
    sources: Record<string, string>;
    children?: import("svelte").Snippet<[any]>;
  }

  const { sources, children }: Props = $props();

  let workspace: WorkspaceAPI = $state()!;

  onMount(async () => {
    const py = await getPy({ workspace: true });
    workspace = py.pyimport("workspace.WorkspaceAPI")(py.toPy(sources));
  });

  onDestroy(() => {
    workspace?.close();
    workspace?.destroy();
  });
</script>

{@render children?.({ sync: workspace?.sync, save: workspace?.save })}
