<script lang="ts">
  import type { PageData } from "./$types";

  import { query } from "./store";
  import { browser } from "$app/environment";
  import { afterNavigate, goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { Button } from "bits-ui";
  import { onMount } from "svelte";

  export let data: PageData;

  let loadingMore = false;

  $: enough = data.total !== null && data.total <= data.results.length;

  let ref: HTMLDivElement;
  let index = 1;

  let intersecting = !enough;

  afterNavigate(() => {
    index = 1;
    intersecting && startLoadingMore();
  });

  async function startLoadingMore() {
    if (loadingMore || !data.query)
      return;
    loadingMore = true;
    const q = $query;
    // eslint-disable-next-line no-unmodified-loop-condition
    while (intersecting && !enough) {
      const url = new URL(location.href);
      url.searchParams.set("page", String(index + 1));
      const json = await fetch(url, { headers: { accept: "application/json" } }).then(res => res.json());
      if (q === $query) {
        data.results = [...data.results, ...json.results];
        index++;
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

{#if $page.url.searchParams.get("q")}
  <h1 class="text-xl">
    <span class="text-neutral-5">搜索</span>
    <span class="text-neutral-1">{data.query}</span>
    <span class="text-neutral-5">得到</span>
    <span class="text-neutral-1">{data.total ?? "10000+"}</span>
    <span class="text-neutral-5">个结果</span>
  </h1>
{:else}
  <div class="grid aspect-3/2 min-h-xs w-full place-items-center rounded bg-gradient-(from-neutral-8/50 via-neutral-8/25 to-neutral-8/0 to-b)">
    <div class="m-4 flex flex-col gap-2">
      <h1 class="text-lg text-neutral-3 font-275 lg:text-xl">在 PyPI 上搜索</h1>
      <!-- svelte-ignore a11y-autofocus -->
      <input autofocus on:keydown={({ key }) => key === "Enter" && goto(`/pypi?q=${$query}`)} placeholder="包名 / 作者" class="w-full b-b-(1 neutral-6) bg-transparent py-1 text-neutral-3 outline-none focus:b-b-neutral-5 lg:text-lg placeholder-neutral-6" bind:value={$query} type="text">
    </div>
  </div>
{/if}

<div class="relative my-4 flex flex-col gap-3 transition-opacity">
  {#each data.results as { name, version, description = "", updated }}
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
  <div bind:this={ref} class="pointer-events-none invisible absolute bottom-0 h-250vh w-full"></div>
</div>
