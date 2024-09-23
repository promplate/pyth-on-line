<script lang="ts">
  import type { Item } from "$py/notebook/notebook";

  import { highlight } from "../highlight";

  export let code: string;
  export let lang = "text";
  export let items: Item[] = [];

  code = code.replaceAll("\r", "");
</script>

<section class="relative overflow-y-scroll rounded-md not-prose [&>pre]:!line-height-relaxed">
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

<style>
  section :global(pre) {
    --uno: font-mono overflow-x-scroll;
  }

  section :global(pre *) {
    --uno: font-mono selection:bg-white/10;
  }
</style>
