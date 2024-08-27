<script lang="ts">
  import type { PageServerData } from "./$types";

  import CodeBlock from "$lib/components/CodeBlock.svelte";

  export let data: PageServerData;
</script>

<div class="text-sm [&_.line>span]:select-all [&>*>*]:p-5">
  <CodeBlock lang="json" code={JSON.stringify(data, null, 4)} />
</div>
