<script lang="ts">
  import type { PageProps } from "./$types";

  import Workspace from "../../../Workspace.svelte";

  const { data, params }: PageProps = $props();
</script>

{#key `${params.owner}/${params.repo}`}
  <Workspace sources={data.sources} />
{/key}
