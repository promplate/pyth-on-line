<script lang="ts">
  import type { Snippet } from "svelte";

  import { tick } from "svelte";

  let { show = $bindable(), closeOnClickOutside = false, cleanup = null, children, backdrop }: {
    show: boolean;
    closeOnClickOutside?: boolean;
    cleanup?: (() => any) | null;
    children?: Snippet<[() => void]>;
    backdrop?: Snippet<[() => void]>;
  } = $props();

  function close() {
    show = false;
    tick().finally(cleanup);
  }
</script>

{#if backdrop}
  {@render backdrop(close)}
{:else}
  {#if closeOnClickOutside}
    <div role="presentation" class={["fixed inset-0 transition duration-1000", { show, "pointer-events-none": !show }]} onclick={close} />
  {:else}
    <div class={["pointer-events-none fixed inset-0 transition duration-1000", { show }]} />
  {/if}
{/if}

{#if show}
  <div class="pointer-events-none fixed inset-0 grid place-items-center [&>*]:pointer-events-auto">
    {@render children?.(close)}
  </div>
{/if}

<style>
  div.show {
    --uno: backdrop-grayscale;
  }
</style>
