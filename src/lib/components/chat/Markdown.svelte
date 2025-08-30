<script lang="ts">
  import type { ConsoleAPI } from "$py/console/console";

  import Router from "../markdown/Router.svelte";
  import WithMarkdown from "../reusable/WithMarkdown.svelte";
  import OverrideCode from "./Code.svelte";

  interface Props {
    text: string;
    runCode: (source: string) => any;
    inspect: typeof ConsoleAPI.prototype.inspect;
  }

  const { text, runCode, inspect }: Props = $props();
</script>

<WithMarkdown>
  {#snippet children({ parse })}
    <Router node={parse(text)} OverrideCode={OverrideCode as any} codeProps={{ runCode }} inlineCodeProps={{ inspect }} />
  {/snippet}
</WithMarkdown>
