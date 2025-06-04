<script lang="ts">
  import Router from "../markdown/Router.svelte";
  import WithMarkdown from "../reusable/WithMarkdown.svelte";
  import OverrideCode from "./Code.svelte";
  import HeadlessNotebook from "$lib/components/notebook/HeadlessNotebook.svelte";

  export let text: string;
</script>

<HeadlessNotebook let:pyNotebook>
  <WithMarkdown let:parse>
    <Router node={parse(text)} {OverrideCode} codeProps={{ pyNotebook }} inlineCodeProps={{ watch: pyNotebook?.watch }} />
  </WithMarkdown>
</HeadlessNotebook>
