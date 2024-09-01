<script lang="ts">
  import type { PageData } from "./$types";

  import BaseMarkdown from "$lib/components/markdown/BaseMarkdown.svelte";

  export let data: PageData;

  const { name, version, description, updated, tags, readme } = data;
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

  <main class="mt-4">
    <BaseMarkdown text={readme} />
  </main>

</div>

<style>
  main :global(h1) {
    --uno: text-4xl font-200;
  }
  main :global(h2) {
    --uno: text-2xl font-250;
  }
  main :global(h3) {
    --uno: text-lg font-300;
  }
</style>
