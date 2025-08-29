<script lang="ts">
  import { tick } from "svelte";
  import Portal from "svelte-portal";
  import { run } from "svelte/legacy";

  interface Props {
    target: HTMLElement;
    show: boolean;
    onHide?: () => void;
    children?: import("svelte").Snippet;
  }

  const {
    target,
    show,
    onHide = () => {},
    children,
  }: Props = $props();

  let position = $state({ top: 0, left: 0 });
  let div: HTMLDivElement = $state()!;

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

  run(() => {
    show && updatePosition();
  });

  const top = $derived(`${position.top}px`);
  const left = $derived(`${position.left}px`);

  let showing = $state(show);

  async function maybeFadeIn(show: boolean) {
    if (show && !showing) {
      await tick();
      showing = show;
    }
  }

  run(() => {
    maybeFadeIn(show);
  });
</script>

{#if show || showing}
  <Portal>
    {@const hiding = !show || !showing}
    <div ontransitionend={() => [(showing = show), !show && onHide()]} class:op-0={hiding} class:pointer-events-none={hiding} class="fixed transition-opacity" style:top style:left bind:this={div}>
      {@render children?.()}
    </div>
  </Portal>
{/if}
