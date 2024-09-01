<script lang="ts">
  import { spring } from "svelte/motion";

  export let show = false;

  export let progress = newStore();

  function newStore() {
    return spring(0, {
      stiffness: 0.1,
      damping: 1,
      precision: 0.001,
    });
  }

  export let reset = () => progress = newStore();
</script>

<slot value={$progress} />

<div on:transitionend={() => !show && reset()} class="relative my-4 h-2px overflow-hidden rounded-full" class:hide={!show}>
  <div class="absolute left-0 h-full rounded-full bg-neutral-2" style:right="{100 - $progress * 100}%" />
</div>

<style>
  .hide {
    --uno: op-0 transition-opacity duration-500 delay-50;
  }
</style>
