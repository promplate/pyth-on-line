<script lang="ts">
  import type { PageProps } from "./$types";

  import Workspace from "../../../Workspace.svelte";
  import { updateMetadata } from "#lib/seo.js";

  const { data, params }: PageProps = $props();

  updateMetadata(() => ({ ogTitle: `${params.owner}/${params.repo} - Python Workspace`, ogDescription: `Explore and run ${params.owner}/${params.repo} in your browser.` }));
</script>

{#key `${params.owner}/${params.repo}`.toLowerCase()}
  <Workspace sources={data.sources} />
{/key}
