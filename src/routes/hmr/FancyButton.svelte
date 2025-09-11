<script lang="ts">
  export let href: string;
  export let text: string;
  export let highlighted: boolean = false;
  let first = highlighted;
</script>

<a {href} class="fancy-button group" class:highlighted class:first>
  <span class="fancy-button-text">{text}</span>
  <div class="fancy-button-overlay">
    <span>{text}</span>
    <div class="i-lucide-arrow-right size-4 -translate-y-0.1" />
  </div>
  <div class="fancy-button-particle" on:transitionend|once={() => (first = false)} />
</a>

<style>
  .fancy-button {
    --uno: relative w-44 overflow-hidden rounded-full bg-neutral-8 px-4 py-3 text-center text-sm text-neutral-1 font-semibold focus:outline-none;
  }

  .fancy-button-text {
    --uno: inline-block translate-x-2 transition-all duration-300 -translate-y-0.1;
  }

  .group:hover .fancy-button-text,
  .highlighted .fancy-button-text,
  .fancy-button:focus-visible .fancy-button-text {
    --uno: op-0 -translate-x-3;
  }

  .fancy-button-overlay {
    --uno: absolute top-0 z-10 h-full w-full flex translate-x-2 items-center justify-center gap-1.5 text-neutral-7 op-0 transition-all duration-300;
  }

  .group:hover .fancy-button-overlay,
  .highlighted .fancy-button-overlay,
  .fancy-button:focus-visible .fancy-button-overlay {
    --uno: op-100 -translate-x-3;
  }

  .fancy-button-particle {
    --uno: absolute left-23% top-[calc(50%-0.25rem)] size-2 rounded-full bg-white transition-all duration-300;
  }

  .group:hover .fancy-button-particle,
  .highlighted .fancy-button-particle,
  .fancy-button:focus-visible .fancy-button-particle {
    --uno: left-0 top-0 size-full scale-120 bg-white ease-out;
  }

  .first * {
    --uno: duration-450;
  }
</style>
