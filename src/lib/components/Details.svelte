<script lang="ts">
  interface Props {
    summary?: string;
    children?: import("svelte").Snippet;
  }

  const { summary = "", children }: Props = $props();
</script>

<details>
  {#if summary}
    <summary>{summary}</summary>
  {/if}
  {@render children?.()}
</details>
