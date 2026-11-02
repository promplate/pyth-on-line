<script lang="ts">
  import type { PageProps } from "./$types";

  import Workspace from "../../Workspace.svelte";
  import { updateMetadata } from "#lib/seo.js";

  const { data, params }: PageProps = $props();

  updateMetadata(() => ({ ogTitle: `${params.gist_id} - GitHub Gist`, ogDescription: `Explore and run GitHub gist ${params.gist_id} in your browser.` }));
</script>

{#key params.gist_id}
  <Workspace sources={data.sources} />
{/key}
