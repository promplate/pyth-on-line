<script lang="ts">
  import type { Spring } from "svelte/motion";

  import { search } from "./store";
  import { afterNavigate, beforeNavigate } from "$app/navigation";
  import Progress from "$lib/components/Progress.svelte";
  import { Button } from "bits-ui";

  let showBar = false;

  let progress: Spring<number>;
  let reset: () => any;

  beforeNavigate(async () => {
    reset();
    showBar = true;
    progress.set(0.25, { soft: true });
  });

  afterNavigate(() => {
    progress.set(2, { soft: 1 });
    showBar = false;
  });
</script>

<div class="m-4 w-[calc(100%-2rem)] self-center 2xl:(m-10 w-4xl) lg:(m-7 w-2xl) md:m-6 sm:(m-5 w-xl) xl:(m-8 w-3xl) [&>article]:(lg:text-3.75 xl:text-base)">

  <nav class="w-full flex flex-row items-center justify-between gap-2 text-sm lg:text-base [&>a:hover]:op-80 [&>a]:(op-50 transition)">
    <Button.Root href="/">Home</Button.Root>
    <input bind:value={$search} class="w-xs rounded-sm bg-neutral-6/10 px-0.5em py-0.3em text-neutral-4 outline-none -my-0.3em sm:w-sm placeholder-neutral-6" placeholder="search" type="text">
    <Button.Root href="https://github.com/promplate/pyth-on-line"><div class="i-mdi-github text-xl" /></Button.Root>
  </nav>

  <Progress show={showBar} bind:progress bind:reset />

  <slot />

</div>
