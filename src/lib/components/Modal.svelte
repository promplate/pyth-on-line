<script context="module">
  let counter = 0;
</script>

<script lang="ts">
  import { tick } from "svelte";

  export let show: boolean;
  export let closeOnClickOutside = false;
  export let cleanup: (() => any) | null = null;

  function close() {
    show = false;
    tick().finally(cleanup);
  }

  $: count = show ? ++counter : -1;
</script>

<slot name="backdrop" {close}>
  {#if closeOnClickOutside}
    <div role="presentation" class="fixed inset-0 transition duration-1000" class:show style:z-index={count} class:pointer-events-none={!show} on:click={close} />
  {:else}
    <div class="pointer-events-none fixed inset-0 transition duration-1000" class:show style:z-index={count} />
  {/if}
</slot>

{#if show}
  <slot {close}>
    <div class="pointer-events-none fixed inset-0 grid place-items-center [&>*]:pointer-events-auto" style:z-index={count}>
      <slot name="content" {close} />
    </div>
  </slot>
{/if}

<style>
  div.show {
    --uno: backdrop-grayscale;
  }
</style>
