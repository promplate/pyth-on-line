<script lang="ts">
  import { fly } from "svelte/transition";

  export let title: string;
</script>

<div class="fixed inset-0 z--1 grid place-items-center">
  <div class="flex flex-col gap-10">
    <h1 class="w-full gap-1 text-xl font-sans tracking-wide">
      {#each title.split(" ") as char, i}
        {#if i} <span> </span> {/if}
        {@const t = Math.random() * (i + 1)}
        <span class="inline-block" in:fly|global={{ delay: t * 50, duration: t * 40 + 300, y: Math.random() * 5 }}>{char}</span>
      {/each}
    </h1>
    <div class="flex flex-col gap-4 [&>*]:(w-fit flex flex-row items-center gap-2 b-2 b-neutral-8 rounded-lg px-3 py-2 text-sm transition) -translate-y-5 [&>*:hover]:bg-neutral-8">
      <slot />
    </div>
  </div>
</div>
