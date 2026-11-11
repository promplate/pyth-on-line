<script lang="ts">
  import type { ConsoleAPI, Inspection } from "#py/console/console.js";
  import type { NotebookAPI } from "#py/notebook/notebook.js";
  import type { InlineCode, Node } from "mdast";

  import Tooltip from "../Tooltip.svelte";
  import { on } from "svelte/events";
  import { createSubscriber } from "svelte/reactivity";

  const { node, inspect = null, watch = null }: {
    node: Node;
    inspect?: typeof ConsoleAPI.prototype.inspect | null;
    watch?: typeof NotebookAPI.prototype.watch | null;
  } = $props();

  let ref = $state<HTMLElement>();
  const tooltipId = $props.id();
  const focusTarget = $derived(ref?.closest("a") ?? ref);

  const inlineCode = $derived(node as InlineCode);

  let show = $state(false);
  let lastInspection = $state.raw<Inspection>();

  const readInspection = $derived.by(() => {
    const expression = inlineCode.value;
    const startWatching = watch;
    let current: Inspection | undefined;
    // Each expression/watch pair owns its snapshot and subscription, including late callbacks.
    const subscribe = createSubscriber(update => startWatching?.(expression, (result) => {
      current = result;
      update();
    }));

    return () => {
      if (startWatching)
        subscribe();
      return current ?? inspect?.(expression);
    };
  });

  const inspection = $derived(show ? readInspection() : lastInspection);

  function hide() {
    lastInspection = inspection;
    show = false;
  }

  function hideUnlessActive() {
    if (!ref?.matches(":hover") && !focusTarget?.matches(":focus"))
      hide();
  }

  $effect(() => {
    if (!focusTarget)
      return;
    const offFocus = on(focusTarget, "focus", () => show = true);
    const offBlur = on(focusTarget, "blur", hideUnlessActive);
    return () => [offFocus(), offBlur()];
  });

  $effect(() => {
    const target = focusTarget;
    if (!target || !show || inspection === undefined)
      return;
    target.setAttribute("aria-describedby", [target.getAttribute("aria-describedby"), tooltipId].filter(Boolean).join(" "));
    return () => {
      const ids = target.getAttribute("aria-describedby")?.split(" ").filter(id => id !== tooltipId).join(" ");
      if (ids)
        target.setAttribute("aria-describedby", ids);
      else
        target.removeAttribute("aria-describedby");
    };
  });

  $effect(() => {
    if (!show)
      return;
    return on(window, "keydown", (event) => {
      if (event.key === "Escape")
        hide();
    });
  });

  const { outerColor, classColor, valueColor } = $derived.by(() => {
    switch (inspection?.type) {
      case "class": {
        return { outerColor: "ring-orange-3/80", classColor: "bg-orange-3/10 text-orange-3", valueColor: "text-orange-50" };
      }
      case "exception": {
        return { outerColor: "ring-rose-3/80", classColor: "bg-rose-3/10 text-rose-3", valueColor: "text-rose-50" };
      }
      default: {
        return { outerColor: "ring-blue-3/80", classColor: "bg-blue-3/10 text-blue-3", valueColor: "text-blue-50" };
      }
    }
  });
</script>

{#if inspect || watch}
  <Tooltip target={ref!} show={show && inspection !== undefined}>
    <div id={tooltipId} role="tooltip" aria-hidden={!show} class="{outerColor} max-w-lg flex flex-row items-center gap-1.5 overflow-x-hidden ws-nowrap rounded bg-neutral-8/80 p-1.5 pr-2 text-sm text-xs font-mono ring-(1.5 inset) backdrop-blur -translate-y-0.4em <lg:(text-2.75 ring-1.3) <sm:(text-2.5 ring-1.1)">
      <div class="{classColor} rounded-sm px-1 py-0.5 font-bold <lg:(px-0.75 py-0.25) <sm:(px-0.5 py-0)">{inspection?.class}</div>
      <div class="{valueColor} overflow-x-hidden text-ellipsis">{inspection?.value}</div>
    </div>
  </Tooltip>

  <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
  <code tabindex={focusTarget === ref ? 0 : undefined} onmouseenter={() => show = true} onmouseleave={hideUnlessActive} bind:this={ref}>{inlineCode.value}</code>
{:else}
  <code>{inlineCode.value}</code>
{/if}
