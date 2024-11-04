<script lang="ts">
  import Highlight from "./Highlight.svelte";

  export let text: string;

  // eslint-disable-next-line no-control-regex
  const ansiPattern = /\x1B\[[0-9;]*[mK]/;
</script>

{#if ansiPattern.test(text)}
  <Highlight text={text.replace(/\n$/, "")} lang="ansi" />
{:else}
  {text}
{/if}
