<script lang="ts">
  import { spring } from "svelte/motion";

  function newStore() {
    return spring(0, {
      stiffness: 0.1,
      damping: 1,
      precision: 0.001,
    });
  }

  interface Props {
    show?: boolean;
    progress?: any;
    reset?: any;
    children?: import("svelte").Snippet<[any]>;
  }

  let {
    show = false,
    progress = $bindable(newStore()),
    reset = $bindable(() => progress = newStore()),
    children,
  }: Props = $props();
</script>

{@render children?.({ value: $progress })}

<div ontransitionend={() => !show && reset()} class="relative h-2px overflow-hidden rounded-full" class:hide={!show}>
  <div class="absolute left-0 h-full rounded-full bg-neutral-2" style:right="{100 - $progress * 100}%"></div>
</div>

<style>
  .hide {
    --uno: op-0 transition-opacity duration-500 delay-50;
  }
</style>
