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
  let focusedExpressions = $state.raw<string[]>();
  let lastInspections = $state.raw<{ expression: string; inspection: Inspection | undefined }[]>([]);
  const expressions = $derived(focusedExpressions ?? [inlineCode.value]);

  const readers = $derived(expressions.map((expression) => {
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
      return { expression, inspection: current ?? inspect?.(expression) };
    };
  }));

  const inspections = $derived(show ? readers.map(read => read()) : lastInspections);
  const hasInspection = $derived(inspections.some(({ inspection }) => inspection !== undefined));

  function hide() {
    lastInspections = inspections;
    show = false;
    focusedExpressions = undefined;
  }

  function showFromFocus() {
    if (focusTarget !== ref) {
      const codes = [...focusTarget!.querySelectorAll("code")];
      if (codes[0] !== ref) {
        hide();
        return;
      }
      // One link has one keyboard stop, so its first code owns the combined inspection.
      focusedExpressions = codes.map(code => code.textContent ?? "");
    }
    show = true;
  }

  function showFromPointer() {
    if (focusTarget !== ref && focusTarget?.matches(":focus"))
      return;
    focusedExpressions = undefined;
    show = true;
  }

  function hideUnlessActive() {
    if (!ref?.matches(":hover") && !focusTarget?.matches(":focus"))
      hide();
    else if (!focusTarget?.matches(":focus"))
      focusedExpressions = undefined;
  }

  $effect(() => {
    if (!focusTarget)
      return;
    const offFocus = on(focusTarget, "focus", showFromFocus);
    const offBlur = on(focusTarget, "blur", hideUnlessActive);
    return () => [offFocus(), offBlur()];
  });

  $effect(() => {
    const target = focusTarget;
    if (!target || !show || !hasInspection)
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

  function colors(inspection: Inspection) {
    switch (inspection.type) {
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
  }
</script>

{#if inspect || watch}
  <Tooltip target={focusedExpressions ? focusTarget! : ref!} show={show && hasInspection}>
    <div id={tooltipId} role="tooltip" aria-hidden={!show} class="flex flex-col gap-1">
      {#each inspections as { expression, inspection }}
        {#if inspection !== undefined}
          {@const { outerColor, classColor, valueColor } = colors(inspection)}
          <div class="{outerColor} max-w-lg flex flex-row items-center gap-1.5 overflow-x-hidden ws-nowrap rounded bg-neutral-8/80 p-1.5 pr-2 text-sm text-xs font-mono ring-(1.5 inset) backdrop-blur -translate-y-0.4em <lg:(text-2.75 ring-1.3) <sm:(text-2.5 ring-1.1)">
            {#if inspections.length > 1}
              <span class="overflow-x-hidden text-ellipsis text-neutral-4">{expression}:</span>
            {/if}
            <div class="{classColor} rounded-sm px-1 py-0.5 font-bold <lg:(px-0.75 py-0.25) <sm:(px-0.5 py-0)">{inspection.class}</div>
            <div class="{valueColor} overflow-x-hidden text-ellipsis">{inspection.value}</div>
          </div>
        {/if}
      {/each}
    </div>
  </Tooltip>

  <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
  <code tabindex={focusTarget === ref ? 0 : undefined} onmouseenter={showFromPointer} onmouseleave={hideUnlessActive} bind:this={ref}>{inlineCode.value}</code>
{:else}
  <code>{inlineCode.value}</code>
{/if}
