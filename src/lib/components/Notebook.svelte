<script lang="ts">
  import Node from "./notebook/Node.svelte";
  import WithMarkdown from "./reusable/WithMarkdown.svelte";
  import WithConsole from "$lib/components/notebook/HeadlessNotebook.svelte";

  export let text: string;
</script>

<WithConsole let:pyNotebook>
  <WithMarkdown let:parse>
    <Node node={parse(text)} {pyNotebook} />
  </WithMarkdown>
</WithConsole>
