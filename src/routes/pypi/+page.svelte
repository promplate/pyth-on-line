<script lang="ts">
  import type { PageServerData } from "./$types";

  import { search } from "./store";
  import { browser } from "$app/environment";
  import { goto } from "$app/navigation";
  import CodeBlock from "$lib/components/CodeBlock.svelte";

  export let data: PageServerData;

  let loading = false;

  $search = data.query;

  $: if (browser && $search) {
    const url = new URL(location.href);
    url.searchParams.set("q", $search);
    loading = true;
    goto(url, { replaceState: true, keepFocus: true }).finally(() => loading = false);
  }
</script>

<div class="text-sm [&_.line>span]:select-all [&>*>*]:p-5" class:op-50={loading}>
  <CodeBlock lang="json" code={JSON.stringify(data, null, 4)} />
</div>
