<script lang="ts">
  import type { ConsoleAPI } from "#py/console/console.js";

  import Router from "../markdown/Router.svelte";
  import WithMarkdown from "../reusable/WithMarkdown.svelte";
  import OverrideCode from "./Code.svelte";

  const { text, runCode, inspect }: { text: string; runCode: (source: string) => any; inspect: typeof ConsoleAPI.prototype.inspect } = $props();
</script>

<WithMarkdown>
  {#snippet children(parse)}
    <Router node={parse(text)} {OverrideCode} codeProps={{ runCode }} inlineCodeProps={{ inspect }} />
  {/snippet}
</WithMarkdown>
