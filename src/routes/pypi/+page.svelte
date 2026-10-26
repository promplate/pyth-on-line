<script lang="ts">
  import type { PageData } from "./$types";

  import { getSearchState } from "./store";
  import { afterNavigate, goto } from "$app/navigation";
  import { page } from "$app/state";
  import { updateMetadata } from "$lib/seo";
  import { Button } from "bits-ui";
  import { tick } from "svelte";

  updateMetadata({ ogTitle: "PyPI Explorer", ogDescription: "Search and explore Python packages from the PyPI directly in your browser." });

  const { data }: { data: PageData } = $props();
  const searchState = getSearchState();
  let additionalResults = $state.raw<PageData["results"]>([]);
  const packageKey = (name: string) => name.toLowerCase().replace(/[-_.]+/g, "-");
  const results = $derived([...new Map([...data.results, ...additionalResults].map(item => [packageKey(item.name), item])).values()]);

  let loadingMore = false;

  // Pagination counts received records even when ranked pages overlap in the rendered list.
  const enough = $derived(data.total !== null && data.total <= data.results.length + additionalResults.length);

  let ref: HTMLDivElement;
  let index = 1;
  let generation = 0;
  let intersecting = false;

  afterNavigate(() => {
    generation++;
    additionalResults = [];
    index = 1;
    loadingMore = false;
    intersecting && startLoadingMore();
  });

  async function startLoadingMore() {
    if (loadingMore || !data.query)
      return;
    loadingMore = true;
    const currentGeneration = generation;
    try {
      // `enough` is derived from the results appended below.
      // eslint-disable-next-line no-unmodified-loop-condition
      while (intersecting && !enough) {
        const url = new URL(`${location.pathname}/~search${location.search}`, location.origin);
        url.searchParams.set("page", String(index + 1));
        const json = await fetch(url, { headers: { accept: "application/json" } }).then(res => res.json());
        // A response from the previous search must not append to the new results.
        if (currentGeneration !== generation)
          return;
        additionalResults = [...additionalResults, ...json.results];
        index++;
        await tick();
        intersecting = ref.getBoundingClientRect().top < innerHeight;
      }
    }
    finally {
      if (currentGeneration === generation)
        loadingMore = false;
    }
  }

  function observeResults(node: HTMLDivElement) {
    const observer = new IntersectionObserver(([{ isIntersecting }]) => {
      intersecting = isIntersecting;
      intersecting && startLoadingMore();
    });
    observer.observe(node);
    return () => {
      generation++;
      observer.disconnect();
    };
  }
</script>

{#if page.url.searchParams.get("q")}
  <h1 class="text-xl">
    <span class="text-neutral-1">{data.total}</span>
    <span class="text-neutral-5">Results for</span>
    <span class="text-neutral-1">{data.query}</span>
  </h1>
{:else}
  <div class="grid aspect-3/2 min-h-xs w-full place-items-center rounded bg-gradient-(from-neutral-8/50 via-neutral-8/25 to-neutral-8/0 to-b)">
    <div class="m-4 flex flex-col gap-2">
      <h1 class="text-lg text-neutral-3 font-275 lg:text-xl">Welcome to the PyPI Explorer</h1>
      <!-- svelte-ignore a11y-autofocus -->
      <input autofocus onkeydown={({ key }) => key === "Enter" && goto(`/pypi?q=${searchState.query}`)} placeholder="search something ..." class="w-full b-b-(1 neutral-6) bg-transparent py-1 text-neutral-3 outline-none focus:b-b-neutral-5 lg:text-lg placeholder-neutral-6" bind:value={() => searchState.query, searchState.setQuery} type="text">
    </div>
  </div>
{/if}

<div class="relative my-4 flex flex-col gap-3 transition-opacity">
  {#each results as { name, version, description = "", updated } (packageKey(name))}
    <Button.Root class="flex flex-col gap-1 px-3 py-2 ring-(1.2 neutral-8) hover:ring-neutral-5" href="/pypi/{name}">
      <div class="flex flex-row items-center gap-1.5 ws-nowrap">
        <h2 class="text-lg text-neutral-1">{name}</h2>
        {#if version}
          <code class="rounded-sm bg-neutral-4/10 px-1 text-sm text-neutral-4">{version}</code>
        {/if}
        <div class="w-full text-right text-neutral-4 text-neutral-7 <sm:text-sm">{updated}</div>
      </div>
      <h3 class="text-xs text-neutral-5 sm:text-sm">{description}</h3>
    </Button.Root>
  {/each}
  <div bind:this={ref} {@attach observeResults} class="pointer-events-none invisible absolute bottom-0 h-250vh w-full"></div>
</div>
