<script>
  import text from "./example.md?raw";
  import BaseMarkdown from "$lib/components/markdown/BaseMarkdown.svelte";
</script>

<div class="mx-auto my-10 w-lg rounded bg-white/5 p-5">
  <BaseMarkdown {text} />
</div>
