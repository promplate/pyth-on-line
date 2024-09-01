<script lang="ts">
  import type { PageServerData } from "./$types";

  import { query } from "./store";
  import { browser } from "$app/environment";
  import { afterNavigate, goto } from "$app/navigation";
  import { Button } from "bits-ui";
  import { onMount } from "svelte";

  export let data: PageServerData;

  let navigating = false;
  let loadingMore = false;

  $: if (browser && $query && $query !== data.query) {
    const query = $query;
    const url = new URL(location.href);
    url.searchParams.set("q", query);
    navigating = true;
    goto(url, { replaceState: true, keepFocus: true }).finally(() => query === $query && (navigating = false));
  }

  $: enough = data.total !== null && data.total <= data.results.length;

  let ref: HTMLDivElement;
  let page = 1;

  let intersecting = !enough;

  afterNavigate(() => {
    page = 1;
    intersecting && startLoadingMore();
  });

  async function startLoadingMore() {
    if (loadingMore)
      return;
    loadingMore = true;
    const query = $query;
    // eslint-disable-next-line no-unmodified-loop-condition
    while (intersecting && !enough) {
      const url = new URL(location.href);
      url.searchParams.set("page", String(page + 1));
      const json = await fetch(url, { headers: { accept: "application/json" } }).then(res => res.json());
      if (query === $query) {
        data.results = [...data.results, ...json.results];
        page++;
        await new Promise(resolve => setTimeout(resolve, 10));
      }
      else {
        return;
      }
    }
    loadingMore = false;
  }

  $: if (browser && intersecting) {
    startLoadingMore();
  }

  onMount(() => {
    new IntersectionObserver(([{ isIntersecting }]) => {
      intersecting = isIntersecting;
    }).observe(ref);
  });
</script>

<h1 class="text-xl">
  <span class="text-neutral-1">{data.total}</span>
  <span class="text-neutral-5">Results for</span>
  <span class="text-neutral-1">{data.query}</span>
</h1>

<div class="relative my-4 flex flex-col gap-3 transition-opacity" class:op-50={navigating}>
  {#each data.results as { name, version, description = "", updated }}
    <Button.Root class="flex flex-col gap-1 px-3 py-2 ring-(1.2 neutral-8) hover:ring-neutral-5" href="/pypi/{name}">
      <div class="flex flex-row items-center gap-1.5 ws-nowrap">
        <h2 class="text-lg text-neutral-1">{name}</h2>
        <code class="rounded-sm bg-neutral-4/10 px-1 text-sm text-neutral-4">{version}</code>
        <div class="w-full text-right text-neutral-4 text-neutral-7 <sm:text-sm">{updated}</div>
      </div>
      <h3 class="text-xs text-neutral-5 sm:text-sm">{description}</h3>
    </Button.Root>
  {/each}
  <div bind:this={ref} class="pointer-events-none invisible absolute bottom-0 h-250vh w-full"></div>
</div>
