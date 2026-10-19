<script lang="ts">
  import type { Code, Node } from "mdast";
  import type { Snippet } from "svelte";

  import UseCopy from "../console/UseCopy.svelte";
  import WithTooltip from "../reusable/WithTooltip.svelte";

  const { node, run = null, fadeIn = false, runnable = null, children }: {
    node: Node;
    run?: ((source: string) => any) | null;
    fadeIn?: boolean;
    runnable?: boolean | null;
    children: Snippet<[Code]>;
  } = $props();

  const code = $derived(node as Code);

  const canRun = $derived(runnable || Boolean(code.lang && run && "python".startsWith(code.lang)));
</script>

{#if code.value}
  <div class="group relative flex flex-col animate-(duration-150 ease-out)" class:animate-fade-in={fadeIn}>

    {@render children(code)}

    <div class="absolute right-0.9em top-0.9em flex flex-row-reverse gap-0.3em transition group-not-hover:(pointer-events-none op-0) [&>button]:(rounded bg-white/5 p-0.6em text-0.725em transition) [&>button:hover]:(bg-white/10)">
      <UseCopy text={code.value}>
        {#snippet children(handleClick)}
          <WithTooltip let:builder tips="Copy">
            <button onclick={handleClick} {...builder} use:builder.action><div class="i-icon-park-twotone-copy" /></button>
          </WithTooltip>
        {/snippet}
      </UseCopy>
      {#if canRun && run}
        <WithTooltip let:builder tips="Run">
          <button onclick={() => run(code.value)} {...builder} use:builder.action><div class="i-mingcute-play-fill" /></button>
        </WithTooltip>
      {/if}
    </div>
  </div>
{/if}

<style>
  div:not(:has(>div>button:active)) :global(pre > *)  {
    --uno: transition-font-weight duration-400 ease-out;
  }

  div:has(>div>button:active) :global(pre *) {
    --uno: font-black;
  }
</style>
