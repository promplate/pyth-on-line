<script lang="ts">
  import type { Item, NotebookAPI } from "$py/notebook/notebook";

  import { highlight } from "../highlight";
  import Tooltip from "./Tooltip.svelte";
  import { onMount } from "svelte";

  export let code: string;
  export let lang = "text";
  export let items: Item[] = [];
  export let pyNotebook: NotebookAPI | undefined;
  export let enableInspection = false;

  let codeContainer: HTMLElement;
  let tooltipTarget: HTMLElement | null = null;
  let showTooltip = false;
  let inspectionResult: any = null;

  code = code.replaceAll("\r", "");

  // Enable inspection for Python code when pyNotebook is available
  $: actuallyEnableInspection = enableInspection && lang === "python" && pyNotebook;

  function makeTokensInspectable() {
    if (!codeContainer || !actuallyEnableInspection)
      return;

    // Find all spans that contain Python identifiers
    const spans = codeContainer.querySelectorAll("code span span");
    spans.forEach((span) => {
      const text = span.textContent?.trim();
      if (text && /^[a-z_]\w*(\.[a-z_]\w*)*$/i.test(text)) {
        // Skip keywords and special tokens
        const skipTokens = ["import", "from", "def", "class", "if", "else", "elif", "for", "while", "return", "await", "async", "and", "or", "not", "in", "is", "True", "False", "None", "with", "as", "try", "except", "finally", "raise", "break", "continue", "pass", "lambda", "global", "nonlocal", "yield", "assert", "del"];

        if (!skipTokens.includes(text)) {
          span.setAttribute("data-inspectable", "true");
          span.setAttribute("data-token", text);
          span.classList.add("inspectable-token");
        }
      }
    });
  }

  function handleTokenHover(event: MouseEvent) {
    const target = event.target as HTMLElement;

    if (target.hasAttribute("data-inspectable") && pyNotebook) {
      const token = target.getAttribute("data-token");
      if (token) {
        tooltipTarget = target;
        showTooltip = true;

        // Get inspection result
        try {
          inspectionResult = pyNotebook.inspect(token);
          if (!inspectionResult) {
            showTooltip = false;
          }
        }
        catch (e) {
          console.warn("Inspection failed for token:", token, e);
          inspectionResult = null;
          showTooltip = false;
        }
      }
    }
  }

  function handleTokenLeave(event: MouseEvent) {
    showTooltip = false;
    tooltipTarget = null;
    inspectionResult = null;
  }

  onMount(() => {
    if (actuallyEnableInspection) {
      // Set up hover listeners
      codeContainer.addEventListener("mouseover", handleTokenHover);
      codeContainer.addEventListener("mouseleave", handleTokenLeave);

      return () => {
        codeContainer.removeEventListener("mouseover", handleTokenHover);
        codeContainer.removeEventListener("mouseleave", handleTokenLeave);
      };
    }
  });

  // Make tokens inspectable after highlighting is complete
  $: if (actuallyEnableInspection && codeContainer) {
    // Use a timeout to ensure DOM is updated after highlighting
    setTimeout(makeTokensInspectable, 100);
  }
</script>

<section bind:this={codeContainer} class="not-prose relative overflow-y-scroll rounded-md [&>pre]:!line-height-relaxed">
  {#key code}
    {#await highlight(lang, code)}
      <pre class="text-white/70">{code}</pre>
    {:then code}
      {@html code}
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

{#if showTooltip && tooltipTarget && inspectionResult}
  <Tooltip target={tooltipTarget} show={showTooltip} onHide={() => showTooltip = false}>
    <div class="max-w-xs border border-neutral-600 rounded bg-neutral-800/95 px-3 py-2 text-white shadow-lg">
      <div class="mb-1 text-xs text-neutral-300">{inspectionResult.class}</div>
      <div class="break-words text-sm font-mono">{inspectionResult.value}</div>
      {#if inspectionResult.type}
        <div class="mt-1 text-xs text-blue-300">{inspectionResult.type}</div>
      {/if}
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

  section :global(.inspectable-token) {
    cursor: help;
    transition: background-color 0.15s ease;
    border-radius: 2px;
    padding: 1px 2px;
  }

  section :global(.inspectable-token:hover) {
    background-color: rgba(255, 255, 255, 0.1);
  }
</style>
