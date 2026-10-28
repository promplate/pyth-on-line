<script lang="ts">
  import type { PageServerData } from "./$types";

  import { page } from "$app/state";
  import Router from "$lib/components/markdown/Router.svelte";
  import OverrideCode from "$lib/components/notebook/Code.svelte";
  import HeadlessNotebook from "$lib/components/notebook/HeadlessNotebook.svelte";
  import WithMarkdown from "$lib/components/reusable/WithMarkdown.svelte";
  import getPy from "$lib/pyodide";

  const { data }: { data: PageServerData } = $props();

  let text = $state("");
  let loading = $state(true);
  let failed = $state(false);

  $effect(() => {
    const html = data.html;
    const pathname = page.url.pathname;
    let disposed = false;
    loading = true;
    failed = false;

    getPy({ web: true }).then(async (py) => {
      // Navigation can finish before Pyodide startup or conversion; only the current page may publish.
      if (disposed)
        return;
      const nextText = await py.pyimport("web.get_cpython_docs")(html, pathname);
      if (disposed)
        return;
      text = nextText;
      loading = false;
    }).catch((error) => {
      if (disposed)
        return;
      failed = true;
      loading = false;
      console.error(error);
    });

    return () => {
      disposed = true;
    };
  });
</script>

{#if failed}
  <div role="alert" class="grid h-50vh w-full place-items-center rounded-md bg-white/3">
    Unable to load Python documentation. Reload the page to try again.
  </div>
{:else if loading}
  <div class="grid h-50vh w-full place-items-center rounded-md bg-white/3">
    <div class="i-svg-spinners-90-ring-with-bg op-50"></div>
  </div>
{:else}
  <HeadlessNotebook>
    {#snippet children(pyNotebook)}
      <WithMarkdown>
        {#snippet children(parse)}
          <Router node={parse(text)} {OverrideCode} codeProps={{ pyNotebook, heuristics: true }} inlineCodeProps={{ watch: pyNotebook?.watch }} />
        {/snippet}
      </WithMarkdown>
    {/snippet}
  </HeadlessNotebook>
{/if}
