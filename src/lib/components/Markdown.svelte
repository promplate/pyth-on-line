<script lang="ts">
  import type { ConsoleAPI } from "$py/console/console";

  import Node from "./markdown/Node.svelte";
  import WithMarkdown from "./reusable/WithMarkdown.svelte";

  export let text: string;
  export let runCode: (source: string) => any;
  export let inspect: typeof ConsoleAPI.prototype.inspect;
</script>

<WithMarkdown let:parse>
  <Node node={parse(text)} {runCode} {inspect} />
</WithMarkdown>
