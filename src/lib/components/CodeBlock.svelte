<script lang="ts">
  import { highlight } from "../highlight";

  export let code: string;
  export let lang = "text";

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
</section>

<style>
  section :global(pre) {
    --uno: font-mono;
  }

  section :global(pre *) {
    --uno: font-mono selection:bg-white/10;
  }
</style>
