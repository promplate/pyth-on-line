<script lang="ts">
  import type { PageProps } from "./$types";

  import Workspace from "../../Workspace.svelte";

  const { data, params }: PageProps = $props();
</script>

{#key params.gist_id}
  <Workspace sources={data.sources} />
{/key}
