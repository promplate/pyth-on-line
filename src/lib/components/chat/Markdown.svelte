<script lang="ts">
  import type { ConsoleAPI } from "$py/console/console";

  import Router from "../markdown/Router.svelte";
  import WithMarkdown from "../reusable/WithMarkdown.svelte";
  import OverrideCode from "./Code.svelte";

  export let text: string;
  export let runCode: ((source: string) => any) | null = null;
  export let inspect: typeof ConsoleAPI.prototype.inspect | null = null;
</script>

<WithMarkdown let:parse>
  <Router node={parse(text)} {OverrideCode} codeProps={{ runCode }} inlineCodeProps={{ inspect }} />
</WithMarkdown>
