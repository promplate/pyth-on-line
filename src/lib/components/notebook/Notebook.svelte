<script lang="ts">
  import Router from "../markdown/Router.svelte";
  import WithMarkdown from "../reusable/WithMarkdown.svelte";
  import OverrideCode from "./Code.svelte";
  import HeadlessNotebook from "$lib/components/notebook/HeadlessNotebook.svelte";

  interface Props {
    text: string;
  }

  const { text }: Props = $props();
</script>

<HeadlessNotebook>
  {#snippet children({ pyNotebook })}
    <WithMarkdown>
      {#snippet children({ parse })}
        <Router node={parse(text)} {OverrideCode} codeProps={{ pyNotebook }} inlineCodeProps={{ watch: pyNotebook?.watch }} />
      {/snippet}
    </WithMarkdown>
  {/snippet}
</HeadlessNotebook>
