<script lang="ts">
  import WithMarkdown from "../reusable/WithMarkdown.svelte";
  import Router from "./Router.svelte";

  interface Props {
    text: string;
  }

  const { text }: Props = $props();
</script>

<WithMarkdown>
  {#snippet children({ parse })}
    <Router node={parse(text)} />
  {/snippet}
</WithMarkdown>
