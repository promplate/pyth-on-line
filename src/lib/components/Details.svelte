<script lang="ts">
  import type { Snippet } from "svelte";

  const { summary = "", children }: { summary?: string; children?: Snippet } = $props();
</script>

<details>
  {#if summary}
    <summary>{summary}</summary>
  {/if}
  {@render children?.()}
</details>
