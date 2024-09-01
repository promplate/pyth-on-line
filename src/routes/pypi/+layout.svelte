<script lang="ts">
  import type { Spring } from "svelte/motion";

  import { query } from "./store";
  import { afterNavigate, beforeNavigate, goto } from "$app/navigation";
  import { navigating, page } from "$app/stores";
  import Progress from "$lib/components/Progress.svelte";
  import { Button } from "bits-ui";

  let progress: Spring<number>;
  let reset: () => any;

  $query = $page.url.searchParams.get("q");

  beforeNavigate(async () => {
    reset();
    progress.set(0.25);
  });

  afterNavigate(() => {
    progress.set(2, { soft: 1 });
  });

  $: disableSearch = Boolean($navigating) || $page.route.id === "/pypi" && $query === $page.url.searchParams.get("q");

  function search() {
    if (!disableSearch) {
      goto(`/pypi?q=${$query}`, { keepFocus: true });
    }
  }
</script>

<div class="relative mb-4 w-[calc(100%-2rem)] self-center 2xl:(mb-10 w-4xl) lg:(mb-7 w-2xl) md:mb-6 sm:(mb-5 w-xl) xl:(mb-8 w-3xl) [&>article]:(lg:text-3.75 xl:text-base)">

  <header class="sticky top-0 z-1 bg-gradient-(from-neutral-9/95 via-neutral-9/80 to-neutral-9/95 to-t) px-10 pt-4 backdrop-blur-md -mx-10 2xl:pt-10 lg:pt-7 md:pt-6 sm:pt-5 xl:pt-8">

    <nav class="w-full flex flex-row items-center justify-between gap-2 text-sm lg:text-base [&>a:hover]:op-80 [&>a]:(op-50 transition)">
      <Button.Root href="/">Home</Button.Root>
      <div class="max-w-50vw w-xs flex flex-row items-center rounded-sm bg-neutral-6/10 px-0.5em py-0.3em -my-0.3em lg:w-sm">
        <input bind:value={$query} on:keydown={({ key }) => key === "Enter" && search()} class="w-full bg-transparent text-neutral-4 outline-none placeholder-neutral-6" placeholder="search" type="text">
        <button disabled={disableSearch} on:click={search} class="p-0.3em text-neutral-5 -m-0.3em hover:text-neutral-4">
          <div class="i-mingcute-search-line" />
        </button>
      </div>
      <Button.Root href="https://github.com/promplate/pyth-on-line"><div class="i-mdi-github text-xl" /></Button.Root>
    </nav>

    <Progress show={!!$navigating} bind:progress bind:reset />

  </header>

  <slot />

</div>
