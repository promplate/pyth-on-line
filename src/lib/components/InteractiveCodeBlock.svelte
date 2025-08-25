<script lang="ts">
  import type { Inspection } from "$py/console/console";
  import type { Item, NotebookAPI } from "$py/notebook/notebook";

  import { highlight } from "../highlight";
  import Tooltip from "./Tooltip.svelte";

  export let code: string;
  export let lang = "text";
  export let items: Item[] = [];
  export let pyNotebook: NotebookAPI | null = null;

  code = code.replaceAll("\r", "");

  let preElement: HTMLDivElement;
  let hoveredElement: HTMLElement | null = null;
  let showTooltip = false;
  let inspectionData: Inspection | null = null;
  let disposeWatcher: (() => void) | null = null;

  function handleMouseEnter(event: MouseEvent) {
    const target = event.target as HTMLElement;

    if (target.dataset.inspectable && target.dataset.variable && pyNotebook) {
      hoveredElement = target;
      const varName = target.dataset.variable;

      // Get inspection data
      inspectionData = pyNotebook.inspect(varName);

      if (inspectionData) {
        showTooltip = true;

        // Set up reactive watcher for this variable
        if (disposeWatcher) {
          disposeWatcher();
        }
        disposeWatcher = pyNotebook.watch(varName, (newInspection: Inspection) => {
          if (hoveredElement === target) {
            inspectionData = newInspection;
          }
        });
      }
    }
  }

  function handleMouseLeave() {
    showTooltip = false;
    hoveredElement = null;
    inspectionData = null;

    if (disposeWatcher) {
      disposeWatcher();
      disposeWatcher = null;
    }
  }

  function formatInspectionValue(inspection: Inspection): string {
    if (!inspection)
      return "";

    const lines = [
      `Type: ${inspection.class}`,
      `Value: ${inspection.value}`,
    ];

    if (inspection.type) {
      lines.splice(1, 0, `Kind: ${inspection.type}`);
    }

    return lines.join("\n");
  }
</script>

<section class="not-prose relative overflow-y-scroll rounded-md [&>pre]:!line-height-relaxed">
  {#key code}
    {#await highlight(lang, code, pyNotebook !== null)}
      <pre class="text-white/70">{code}</pre>
    {:then highlightedCode}
      <div
        bind:this={preElement}
        role="presentation"
        on:mouseenter={handleMouseEnter}
        on:mouseleave={handleMouseLeave}
        on:mousemove={handleMouseEnter}
      >{@html highlightedCode}</div>
    {/await}
  {/key}
  {#if items.length}
    <div class="m-2 flex flex-col ws-pre-wrap px-1em text-0.8em line-height-relaxed font-mono">
      {#each items as { type, text }}
        {#if type === "out"}
          <div class="text-yellow-2">{text}</div>
        {/if}
        {#if type === "err"}
          <div class="text-red-4">{text}</div>
        {/if}
        {#if type === "repr"}
          <div class="text-cyan-2">{text}</div>
        {/if}
      {/each}
    </div>
  {/if}
</section>

{#if showTooltip && hoveredElement && inspectionData}
  <Tooltip
    target={hoveredElement}
    show={showTooltip}
    onHide={() => { showTooltip = false; }}
  >
    <div class="max-w-sm border border-neutral-6/30 rounded bg-neutral-8/95 px-2 py-1.5 text-xs text-white shadow-lg backdrop-blur-sm">
      <div class="whitespace-pre-line font-mono">
        {formatInspectionValue(inspectionData)}
      </div>
    </div>
  </Tooltip>
{/if}

<style>
  section :global(pre) {
    --uno: font-mono overflow-x-scroll;
  }

  section :global(pre *) {
    --uno: font-mono selection:bg-white/10;
  }

  section :global([data-inspectable="true"]) {
    --uno: cursor-help border-b border-dotted border-neutral-4/40 transition-colors hover:border-neutral-3/60 hover:bg-white/5;
  }
</style>
