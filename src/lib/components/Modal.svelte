<script lang="ts">
  import { tick } from "svelte";

  interface Props {
    show: boolean;
    closeOnClickOutside?: boolean;
    cleanup?: (() => any) | null;
    backdrop?: import("svelte").Snippet<[any]>;
    children?: import("svelte").Snippet<[any]>;
  }

  let {
    show = $bindable(),
    closeOnClickOutside = false,
    cleanup = null,
    backdrop,
    children,
  }: Props = $props();

  function close() {
    show = false;
    tick().finally(cleanup);
  }
</script>

{#if backdrop}{@render backdrop({ close })}{:else}
  {#if closeOnClickOutside}
    <div role="presentation" class="fixed inset-0 transition duration-1000" class:show class:pointer-events-none={!show} onclick={close}></div>
  {:else}
    <div class="pointer-events-none fixed inset-0 transition duration-1000" class:show></div>
  {/if}
{/if}

{#if show}
  <div class="pointer-events-none fixed inset-0 grid place-items-center [&>*]:pointer-events-auto">
    {@render children?.({ close })}
  </div>
{/if}

<style>
  div.show {
    --uno: backdrop-grayscale;
  }
</style>
