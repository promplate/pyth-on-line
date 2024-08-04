<script lang="ts">
  import { tick } from "svelte";

  export let show: boolean;
  export let closeOnClickOutside = false;
  export let cleanup: (() => any) | null = null;

  function close() {
    show = false;
    tick().finally(cleanup);
  }
</script>

<slot name="backdrop" {close}>
  {#if closeOnClickOutside}
    <div role="presentation" class="fixed inset-0 transition duration-1000" class:show class:pointer-events-none={!show} on:click={close} />
  {:else}
    <div class="pointer-events-none fixed inset-0 transition duration-1000" class:show />
  {/if}
</slot>

{#if show}
  <div class="pointer-events-none fixed inset-0 grid place-items-center [&>*]:pointer-events-auto">
    <slot {close} />
  </div>
{/if}

<style>
  div.show {
    --uno: backdrop-grayscale;
  }
</style>
