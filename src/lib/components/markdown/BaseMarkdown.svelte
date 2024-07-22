<script lang="ts">
  import WithMarkdown from "../reusable/WithMarkdown.svelte";
  import Router from "./Router.svelte";

  export let text: string;
</script>

<WithMarkdown let:parse>
  <Router node={parse(text)} />
</WithMarkdown>
