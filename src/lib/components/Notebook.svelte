<script lang="ts">
  import Markdown from "$lib/components/Markdown.svelte";
  import WithConsole from "$lib/components/notebook/HeadlessNotebook.svelte";

  export let text: string;
</script>

<WithConsole let:pyNotebook let:run>
  <Markdown {text} inspect={pyNotebook?.inspect} runCode={run} />
</WithConsole>
