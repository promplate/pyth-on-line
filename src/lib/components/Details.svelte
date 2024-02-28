<script>
  export let summary = "";
</script>

<details>
  {#if summary}
    <summary>{summary}</summary>
  {/if}
  <slot />
</details>
