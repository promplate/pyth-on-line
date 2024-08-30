<script lang="ts">
  import type { PageServerData } from "./$types";

  import { search } from "./store";
  import { browser } from "$app/environment";
  import { goto } from "$app/navigation";
  import { Button } from "bits-ui";

  export let data: PageServerData;

  let loading = false;

  $search = data.query;

  $: if (browser && $search && $search !== data.query) {
    const query = $search;
    const url = new URL(location.href);
    url.searchParams.set("q", query);
    loading = true;
    goto(url, { replaceState: true, keepFocus: true }).finally(() => query === $search && (loading = false));
  }
</script>

<h1 class="text-xl">
  <span class="text-neutral-1">{data.total}</span>
  <span class="text-neutral-5">Results for</span>
  <span class="text-neutral-1">{data.query}</span>
</h1>

<div class="my-4 flex flex-col gap-3 transition-opacity" class:op-50={loading}>
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
</div>
