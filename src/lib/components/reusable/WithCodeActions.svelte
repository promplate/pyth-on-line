<script lang="ts">
  import type { Code, Node } from "mdast";

  import UseCopy from "../console/UseCopy.svelte";
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import { run as run_1 } from "svelte/legacy";

  interface Props {
    node: Node;
    run?: ((source: string) => any) | null;
    fadeIn?: boolean;
    runnable?: boolean | null;
    children?: import("svelte").Snippet<[any]>;
  }

  let {
    node,
    run = null,
    fadeIn = false,
    runnable = $bindable(null),
    children,
  }: Props = $props();

  const code = $derived(node as Code);

  run_1(() => {
    runnable = runnable || Boolean(code.lang && run && "python".startsWith(code.lang));
  });
</script>

{#if code.value}
  <div class="group relative flex flex-col animate-(duration-150 ease-out)" class:animate-fade-in={fadeIn}>

    {@render children?.({ code })}

    <div class="absolute right-0.9em top-0.9em flex flex-row-reverse gap-0.3em transition group-not-hover:(pointer-events-none op-0) [&>button]:(rounded bg-white/5 p-0.6em text-0.725em transition) [&>button:hover]:(bg-white/10)">
      <UseCopy text={code.value}>
        {#snippet children({ handleClick })}
          <WithTooltip tips="Copy">
            {#snippet children({ builder })}
              <button onclick={handleClick} {...builder} use:builder.action><div class="i-icon-park-twotone-copy"></div></button>
            {/snippet}
          </WithTooltip>
        {/snippet}
      </UseCopy>
      {#if runnable && run}
        <WithTooltip tips="Run">
          {#snippet children({ builder })}
            <button onclick={() => run(code.value)} {...builder} use:builder.action><div class="i-mingcute-play-fill"></div></button>
          {/snippet}
        </WithTooltip>
      {/if}
    </div>
  </div>
{/if}

<style>
  div:not(:has(>div>button:active)) :global(pre > *)  {
    --uno: transition-font-weight duration-400 ease-out;
  }

  div:has(:global(>div>button:active)) :global(pre *) {
    --uno: font-black;
  }
</style>
