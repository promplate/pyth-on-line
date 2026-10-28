<script lang="ts">
  import type { Item } from "#py/notebook/notebook.js";

  import { highlight } from "../highlight";

  const { code, lang = "text", items = [] }: { code: string; lang?: string; items?: Item[] } = $props();

  const normalizedCode = $derived(code.replaceAll("\r", ""));
</script>

<section class="not-prose relative overflow-y-scroll rounded-md [&>pre]:!line-height-relaxed">
  <!-- Reset the await block so edits show current plain text while highlighting is pending. -->
  {#key normalizedCode}
    {#await highlight(lang, normalizedCode)}
      <pre class="bg-#121212"><code class="!text-#cdcabe">{normalizedCode}</code></pre>
    {:then html}
      {@html html}
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
