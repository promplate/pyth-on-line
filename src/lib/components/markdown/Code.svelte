<script lang="ts">
  import type { Code, Node } from "mdast";

  import UseCopy from "../console/UseCopy.svelte";
  import CodeBlock from "$lib/components/CodeBlock.svelte";
  import { currentPushBlock } from "$lib/stores";

  export let node: Node;

  $: code = node as Code;
</script>

<div class="group relative flex flex-col">
  <CodeBlock lang={code.lang ?? "text"} code={code.value} />
  <div class="absolute right-0.9em top-0.9em flex flex-row gap-0.3em transition group-not-hover:(pointer-events-none op-0) [&>button]:(rounded bg-white/5 p-0.6em text-0.725em transition) [&>button:hover]:(bg-white/10)">
    <UseCopy text={code.value} let:handleClick>
      <button on:click={handleClick}><div class="i-icon-park-twotone-copy" /></button>
    </UseCopy>
    {#if "python".startsWith(code.lang ?? "")}
      <button on:click={() => $currentPushBlock(`${code.value.trimEnd()}\n`)}><div class="i-mingcute-play-fill" /></button>
    {/if}
  </div>
</div>

<style>
  div:not(:has(>div>button:active)) :global(pre *)  {
    --uno: transition-font-weight duration-400 ease-out;
  }

  div:has(>div>button:active) :global(pre *) {
    --uno: font-black;
  }
</style>
