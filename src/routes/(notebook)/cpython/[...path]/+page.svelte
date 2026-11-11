<script lang="ts">
  import type { PageServerData } from "./$types";

  import Router from "#lib/components/markdown/Router.svelte";
  import OverrideCode from "#lib/components/notebook/Code.svelte";
  import HeadlessNotebook from "#lib/components/notebook/HeadlessNotebook.svelte";
  import WithMarkdown from "#lib/components/reusable/WithMarkdown.svelte";
  import { updateMetadata } from "#lib/seo.js";
  import { page } from "$app/state";

  const { data }: { data: PageServerData } = $props();

  updateMetadata(() => ({ ogTitle: data.title, ogDescription: `Read and run ${data.title} in an interactive notebook.` }));
</script>

{#key page.url.pathname}
  <HeadlessNotebook>
    {#snippet children(pyNotebook)}
      <WithMarkdown>
        <Router node={data.node} {OverrideCode} codeProps={{ pyNotebook, heuristics: true }} inlineCodeProps={{ watch: pyNotebook?.watch }} />
      </WithMarkdown>
    {/snippet}
  </HeadlessNotebook>
{/key}
