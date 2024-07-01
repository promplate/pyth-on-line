<script lang="ts">
  import { highlight } from "../highlight";
  import Portal from "./Portal.svelte";
  import { type SourceRef, saveSource } from "$lib/utils/source";
  import { onMount } from "svelte";

  export let code: string;
  export let collapse = false;
  export let portal = false;
  export let lang = "text";

  export let id: string | null = null;
  export let previous: SourceRef[] = [];

  code = code.replaceAll("\r", "");

  onMount(() => {
    id && saveSource(id, code);
  });

</script>

<section class:shrink-0={!collapse} class="not-prose relative overflow-y-scroll rounded-md [&>pre]:!line-height-relaxed">
  {#key code}
    {#await highlight(lang, code)}
      <pre class="text-white/70">{code}</pre>
    {:then code}
      {@html code}
    {/await}
  {/key}
  {#if portal}
    <Portal source={code} {previous} />
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
