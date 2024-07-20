<script lang="ts">
  import type { Code, Node } from "mdast";

  import UseCopy from "../console/UseCopy.svelte";
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import CodeBlock from "$lib/components/CodeBlock.svelte";

  export let node: Node;
  export let runCode: (source: string) => any;

  $: code = node as Code;

  function run(source: string) {
    if (source.split("\n").at(-1)!.startsWith(" ")) // heuristic to detect multiline input
      runCode(`${source}\n\n`);
    else
      runCode(`${source}\n`);
  }
</script>

{#if code.value}
  <div class="group relative flex flex-col animate-(fade-in duration-150 ease-out)">
    <CodeBlock lang={code.lang ?? "text"} code={code.value} />
    <div class="absolute right-0.9em top-0.9em flex flex-row-reverse gap-0.3em transition group-not-hover:(pointer-events-none op-0) [&>button]:(rounded bg-white/5 p-0.6em text-0.725em transition) [&>button:hover]:(bg-white/10)">
      <UseCopy text={code.value} let:handleClick>
        <WithTooltip let:builder tips="Copy">
          <button on:click={handleClick} {...builder} use:builder.action><div class="i-icon-park-twotone-copy" /></button>
        </WithTooltip>
      </UseCopy>
      {#if code.lang && "python".startsWith(code.lang)}
        <WithTooltip let:builder tips="Run">
          <button on:click={() => run(code.value.trimEnd())} {...builder} use:builder.action><div class="i-mingcute-play-fill" /></button>
        </WithTooltip>
      {/if}
    </div>
  </div>
{/if}

<style>
  div:not(:has(>div>button:active)) :global(pre *)  {
    --uno: transition-font-weight duration-400 ease-out;
  }

  div:has(>div>button:active) :global(pre *) {
    --uno: font-black;
  }
</style>
