<script lang="ts">
  import WithMarkdown from "../reusable/WithMarkdown.svelte";
  import Router from "./Router.svelte";

  const { text }: { text: string } = $props();
</script>

<WithMarkdown>
  {#snippet children(parse)}
    <Router node={parse(text)} />
  {/snippet}
</WithMarkdown>
