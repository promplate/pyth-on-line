<script lang="ts">
  import type { PageData } from "./$types";

  import BaseMarkdown from "#lib/components/markdown/BaseMarkdown.svelte";
  import { updateMetadata } from "#lib/seo.js";

  const { data }: { data: PageData } = $props();

  const { name, version, description, updated, tags, readme } = $derived(data);

  updateMetadata(() => ({ ogTitle: `${name} - PyPI Package`, ogDescription: description || `View details and documentation for ${name} on PyPI.` }));
</script>

<div class="flex flex-col gap-2">

  <h1 class="flex flex-row items-center gap-2 ws-nowrap">
    <div class="text-xl text-neutral-1">{name}</div>
    <code class="rounded-sm bg-neutral-4/10 px-1.5 py-0.5 text-sm text-neutral-3">{version}</code>
    <div class="w-full text-right text-neutral-6 <sm:text-sm">{updated}</div>
  </h1>

  {#if description}
    <h2 class="text-neutral-5 <sm:text-sm">{description}</h2>
  {/if}

  {#if tags.length}
    <h3 class="flex flex-row flex-wrap gap-2">
      {#each tags as tag}
        <div class="rounded-sm px-1.5 py-0.5 text-sm text-neutral-5 ring-(1.2 neutral-5/10) <sm:text-xs">{tag}</div>
      {/each}
    </h3>
  {/if}

  <section class="mt-4">
    <BaseMarkdown text={readme} headingIds />
  </section>

</div>

<style>
  section :global(article) {
    --uno: sm:text-base;
  }
  section :global(:where(h1, h2, h3, h4, h5, h6)) {
    --uno: scroll-mt-28;
  }
  section :global(:where(h1, h2, h3)) {
    --uno: mb-0.5em;
  }
  section :global(h1) {
    --uno: text-2.1em font-200;
  }
  section :global(h2) {
    --uno: text-1.7em font-250;
  }
  section :global(h3) {
    --uno: text-1.3em font-300;
  }
</style>
