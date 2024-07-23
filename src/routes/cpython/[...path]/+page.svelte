<script lang="ts">
  import type { PageServerData } from "./$types";

  import { afterNavigate } from "$app/navigation";
  import Router from "$lib/components/markdown/Router.svelte";
  import OverrideCode from "$lib/components/notebook/Code.svelte";
  import HeadlessNotebook from "$lib/components/notebook/HeadlessNotebook.svelte";
  import WithMarkdown from "$lib/components/reusable/WithMarkdown.svelte";
  import getPy from "$lib/pyodide";
  import { Button } from "bits-ui";
  import { onMount } from "svelte";

  export let data: PageServerData;

  let text = "";
  let loading = true;

  async function refresh() {
    loading = true;
    const py = await getPy({ web: true });
    text = await py.pyimport("web.get_cpython_docs")(data.html);
    loading = false;
  };

  onMount(refresh);
  afterNavigate(refresh);
</script>

<div class="m-4 max-w-xl w-auto self-center lg:m-7 md:m-6 sm:m-5 xl:m-8 2xl:max-w-4xl lg:max-w-2xl xl:max-w-3xl [&>article]:(lg:text-3.75 xl:text-base)">

  <nav class="w-full flex flex-row items-center justify-between gap-2 text-sm lg:text-base [&>a:hover]:op-80 [&>a]:(op-50 transition)">
    <Button.Root href="/">Home</Button.Root>
    <Button.Root href="https://github.com/promplate/pyth-on-line"><div class="i-mdi-github text-xl" /></Button.Root>
  </nav>

  <hr class="invisible h-6">

  {#if loading}
    <div class="grid h-50vh w-xl place-items-center rounded-lg bg-white/3 2xl:w-4xl lg:w-2xl xl:w-3xl">
      <div class="i-svg-spinners-bars-rotate-fade op-80" />
    </div>
  {:else}
    <HeadlessNotebook let:pyNotebook>
      <WithMarkdown let:parse>
        <Router node={parse(text)} {OverrideCode} codeProps={{ pyNotebook, heuristics: true }} inlineCodeProps={{ inspect: pyNotebook?.inspect }} />
      </WithMarkdown>
    </HeadlessNotebook>
  {/if}

</div>
