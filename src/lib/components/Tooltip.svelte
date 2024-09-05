<script lang="ts">
  import { tick } from "svelte";
  import Portal from "svelte-portal";

  export let target: HTMLElement;
  export let show: boolean;

  let position = { top: 0, left: 0 };
  let div: HTMLDivElement;

  async function updatePosition() {
    await tick();

    const rect = target.getBoundingClientRect();
    const divWidth = div.offsetWidth;

    const top = rect.top - div.offsetHeight;

    let left = rect.left;

    if (left + divWidth > window.innerWidth) {
      left = rect.right - divWidth;
    }

    if (left < 0) {
      left = 0;
    }

    position = { top, left };
  }

  $: show && updatePosition();

  $: top = `${position.top}px`;
  $: left = `${position.left}px`;

  let doShow = show;
  $: show && (doShow = true);
  const maybeHide = () => !show && (doShow = false);
</script>

{#if doShow}
  <Portal>
    <div on:transitioncancel={maybeHide} on:transitionend={maybeHide} class:op-0={!show} class:pointer-events-none={!show} class="fixed animate-(fade-in duration-150 ease) transition-opacity" style:top style:left bind:this={div}>
      <slot />
    </div>
  </Portal>
{/if}
