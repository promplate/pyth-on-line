<script lang="ts">
  import type { Snippet } from "svelte";

  const { title, children }: { title: string; children?: Snippet } = $props();
</script>

<div class="fixed inset-0 z--1 grid place-items-center">
  <div class="flex flex-col gap-10">
    <h1 class="w-full gap-1 text-xl tracking-wide font-sans">
      {#each title.split(" ") as char, i}
        {#if i} <span> </span> {/if}
        <span class="word inline-block" style:--index={i}>{char}</span>
      {/each}
    </h1>
    <div class="choices flex flex-col gap-4 [&>*]:(w-fit flex flex-row items-center gap-2 b-2 b-neutral-8 rounded-lg px-3 py-2 text-sm transition) -translate-y-5 [&>*:hover]:bg-neutral-8">
      {@render children?.()}
    </div>
  </div>
</div>

<style>
  .word, .choices > :global(a) {
    animation: enter var(--duration, 500ms) cubic-bezier(0.333333, 1, 0.666667, 1) var(--delay, 0ms) backwards;
  }

  .word {
    --duration: calc(300ms + var(--index) * 40ms);
    --delay: calc(var(--index) * 50ms);
    --y: 2.5px;
  }

  @keyframes enter {
    from {
      opacity: 0;
      transform: translate(var(--x, 0), var(--y, 0));
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .word, .choices > :global(a) {
      animation: none;
    }
  }
</style>
