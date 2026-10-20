<script lang="ts">
  import type { Snippet } from "svelte";

  const { show = false, progress = 0, onhide, children }: { show?: boolean; progress?: number; onhide?: () => void; children?: Snippet<[number]> } = $props();
</script>

{@render children?.(progress)}

<div ontransitionend={() => !show && onhide?.()} class={["relative h-2px overflow-hidden rounded-full", { hide: !show }]}>
  <div class="absolute left-0 h-full rounded-full bg-neutral-2" style:right="{100 - progress * 100}%" />
</div>

<style>
  .hide {
    --uno: op-0 transition-opacity duration-500 delay-50;
  }
</style>
