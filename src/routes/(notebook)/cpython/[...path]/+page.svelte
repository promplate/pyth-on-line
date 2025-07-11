<script lang="ts">
  import type { PageServerData } from "./$types";

  import { afterNavigate } from "$app/navigation";
  import Router from "$lib/components/markdown/Router.svelte";
  import OverrideCode from "$lib/components/notebook/Code.svelte";
  import HeadlessNotebook from "$lib/components/notebook/HeadlessNotebook.svelte";
  import WithMarkdown from "$lib/components/reusable/WithMarkdown.svelte";
  import getPy from "$lib/pyodide";
  import { onMount } from "svelte";

  export let data: PageServerData;

  let text = "";
  let loading = true;

  async function refresh() {
    loading = true;
    const py = await getPy({ web: true });
    text = await py.pyimport("web.get_cpython_docs")(data.html, location.pathname);
    loading = false;
  };

  onMount(refresh);
  afterNavigate(refresh);
</script>

{#if loading}
  <div class="grid h-50vh w-full place-items-center rounded-md bg-white/3">
    <div class="i-svg-spinners-90-ring-with-bg op-50" />
  </div>
{:else}
  <HeadlessNotebook let:pyNotebook>
    <WithMarkdown let:parse>
      <Router node={parse(text)} {OverrideCode} codeProps={{ pyNotebook, heuristics: true }} inlineCodeProps={{ watch: pyNotebook?.watch }} />
    </WithMarkdown>
  </HeadlessNotebook>
{/if}
