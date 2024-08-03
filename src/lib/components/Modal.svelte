<script lang="ts">
  export let show: boolean;
  export let closeOnClickOutside = false;

  function close() {
    show = false;
  }
</script>

<slot name="backdrop">
  {#if closeOnClickOutside}
    <div role="presentation" class="fixed inset-0 transition duration-1000" class:show class:pointer-events-none={!show} on:click={close} />
  {:else}
    <div class="pointer-events-none fixed inset-0 transition duration-1000" class:show />
  {/if}
</slot>

{#if show}
  <slot>
    <div class="pointer-events-none fixed inset-0 grid place-items-center [&>*]:pointer-events-auto">
      <slot name="content" />
    </div>
  </slot>
{/if}

<style>
  div.show {
    --uno: backdrop-grayscale;
  }
</style>
