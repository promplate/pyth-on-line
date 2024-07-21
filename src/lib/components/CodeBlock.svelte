<script lang="ts">
  import type { RunResult } from "$py/notebook/notebook";

  import { highlight } from "../highlight";

  export let code: string;
  export let lang = "text";
  export let result: RunResult | undefined;

  code = code.replaceAll("\r", "");
</script>

<section class="not-prose relative overflow-y-scroll rounded-md [&>pre]:!line-height-relaxed">
  {#key code}
    {#await highlight(lang, code)}
      <pre class="text-white/70">{code}</pre>
    {:then code}
      {@html code}
    {/await}
  {/key}
  {#if result && Object.keys(result).length}
    <div class="m-2 flex flex-col ws-pre-wrap px-1em text-0.8em line-height-relaxed font-mono">
      {#if result.out}
        <div class="text-yellow-2">{result.out}</div>
      {/if}
      {#if result.err}
        <div class="text-red-4">{result.err}</div>
      {/if}
      {#if result.repr}
        <div class="text-cyan-2">{result.repr}</div>
      {/if}
    </div>
  {/if}
</section>

<style>
  section :global(pre) {
    --uno: font-mono;
  }

  section :global(pre *) {
    --uno: font-mono selection:bg-white/10;
  }
</style>
