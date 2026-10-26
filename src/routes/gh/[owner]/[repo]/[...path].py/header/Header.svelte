<script lang="ts">
  import type { HeaderLineData } from "./types";

  import DepLine from "./DepLine.svelte";

  const { headerLines }: { headerLines: HeaderLineData[] } = $props();
</script>

{#each headerLines as line, i}{#if line.kind === "dep"}<DepLine data={line.line} />{:else}{line.text}{/if}{i < headerLines.length - 1 ? "\n" : ""}{/each}
