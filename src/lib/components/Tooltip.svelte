<script lang="ts">
  import type { Snippet } from "svelte";

  import { tick, untrack } from "svelte";
  import Portal from "svelte-portal";

  const { target, show, onHide = () => {}, children }: { target: HTMLElement; show: boolean; onHide?: () => void; children?: Snippet } = $props();

  // Keep the portal mounted during fade-out; an initially open tooltip needs no fade-in.
  let showing = $state(untrack(() => show));

  function position(div: HTMLDivElement) {
    const currentTarget = target;
    if (!show || !currentTarget)
      return;

    // Wait for Portal to attach before measuring; hide, retarget and unmount cancel stale work.
    let disposed = false;
    tick().then(() => {
      if (disposed)
        return;

      const rect = currentTarget.getBoundingClientRect();
      const divWidth = div.offsetWidth;
      const top = rect.top - div.offsetHeight;
      let left = rect.left;

      if (left + divWidth > window.innerWidth)
        left = rect.right - divWidth;
      if (left < 0)
        left = 0;

      div.style.top = `${top}px`;
      div.style.left = `${left}px`;
      showing = true;
    });
    return () => {
      disposed = true;
    };
  }
</script>

{#if show || showing}
  <Portal>
    {@const hiding = !show || !showing}
    <div ontransitionend={() => [(showing = show), !show && onHide()]} class={["fixed transition-opacity", { "op-0": hiding, "pointer-events-none": hiding }]} style:top="0px" style:left="0px" {@attach position}>
      {@render children?.()}
    </div>
  </Portal>
{/if}
