<script lang="ts">
  import { tick } from "svelte";
  import Portal from "svelte-portal";

  export let target: HTMLElement;
  export let show: boolean;
  export let onHide: () => void = () => {};

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

  let showing = show;

  async function maybeFadeIn(show: boolean) {
    if (show && !showing) {
      await tick();
      showing = show;
    }
  }

  $: maybeFadeIn(show);
</script>

{#if show || showing}
  <Portal>
    {@const hiding = !show || !showing}
    <div on:transitionend={() => [(showing = show), !show && onHide()]} class:op-0={hiding} class:pointer-events-none={hiding} class="fixed transition-opacity" style:top style:left bind:this={div}>
      <slot />
    </div>
  </Portal>
{/if}
