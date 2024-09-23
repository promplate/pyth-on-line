<script lang="ts">
  import type { Spring } from "svelte/motion";

  import { query } from "./store";
  import { browser } from "$app/environment";
  import { afterNavigate, beforeNavigate, goto, preloadData } from "$app/navigation";
  import { navigating, page } from "$app/stores";
  import Progress from "$lib/components/Progress.svelte";
  import { Button } from "bits-ui";

  let progress: Spring<number>;
  let reset: () => any;

  $query = $page.url.searchParams.get("q") ?? "";

  beforeNavigate(async () => {
    reset();
    progress.set(0.25);
  });

  afterNavigate(() => {
    progress.set(2, { soft: 1 });
  });

  $: disableSearch = Boolean($navigating) || ($page.route.id === "/pypi" && $query === $page.url.searchParams.get("q"));

  function search() {
    if (!disableSearch) {
      goto(`/pypi?q=${$query}`, { keepFocus: true });
    }
  }

  $: if (browser && $query) {
    const q = $query;
    setTimeout(() => q === $query && preloadData(`/pypi?q=${q}`), 250);
  }
</script>

<section class="sticky top-0 z-1 mb-4 bg-gradient-(from-neutral-9/95 via-neutral-9/80 to-neutral-9/95 to-t) pt-4 backdrop-blur-md 2xl:pt-10 lg:pt-7 md:pt-6 sm:pt-5 xl:pt-8">
  <header class="mx-auto w-[calc(100%-2rem)] 2xl:w-4xl lg:w-2xl sm:w-xl xl:w-3xl">

    <nav class="mb-4 w-full flex flex-row items-center justify-between gap-2 text-sm [&_a]:(text-xl text-neutral-3 transition) lg:text-base [&_a:not(:hover)]:op-60">
      <div class="flex flex-row items-center gap-2">
        <Button.Root href="/">
          <div class="i-tabler-smart-home" />
        </Button.Root>
        <Button.Root href={$page.route.id === "/pypi" ? `https://pypi.org/search?q=${$query}` : `https://pypi.org/project/${$page.params.project}/`} target="_blank">
          <div class="i-tabler-external-link" />
        </Button.Root>
      </div>
      <div class="max-w-50vw w-xs flex flex-row items-center rounded-sm bg-neutral-6/10 px-0.5em py-0.3em transition-background-color -my-0.3em lg:w-sm hover:bg-neutral-6/15 focus-within:!bg-neutral-6/21">
        <input bind:value={$query} on:keydown={({ key }) => key === "Enter" && search()} class="w-full bg-transparent text-neutral-4 outline-none placeholder-neutral-6" placeholder="搜索" type="text">
        <button disabled={disableSearch} on:click={search} class="p-0.3em text-neutral-5 -m-0.3em hover:text-neutral-4">
          <div class="i-mingcute-search-line" />
        </button>
      </div>
      <Button.Root href="https://github.com/promplate/pyth-on-line"><div class="i-mdi-github" /></Button.Root>
    </nav>

    <Progress show={!!$navigating} bind:progress bind:reset />

  </header>
</section>

<div class:navigating={$navigating} class="mb-4 w-[calc(100%-2rem)] self-center transition-opacity duration-500 ease-out 2xl:(mb-10 w-4xl) lg:(mb-7 w-2xl) md:mb-6 sm:(mb-5 w-xl) xl:(mb-8 w-3xl) [&>article]:(lg:text-3.75 xl:text-base)">

  <slot />

</div>

<style>
  .navigating {
    --uno: op-50 duration-1000;
  }
</style>
