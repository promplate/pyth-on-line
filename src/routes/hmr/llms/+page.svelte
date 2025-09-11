<script lang="ts">
  import type { PageData } from "./$types";

  import "@fontsource-variable/jetbrains-mono/wght.css";
  import "@fontsource-variable/jetbrains-mono/wght-italic.css";

  import { browser } from "$app/environment";
  import { page } from "$app/stores";
  import CodeBlock from "$lib/components/CodeBlock.svelte";
  import UseCopy from "$lib/components/console/UseCopy.svelte";
  import Router from "$lib/components/markdown/Router.svelte";
  import WithMarkdown from "$lib/components/reusable/WithMarkdown.svelte";
  import WithTooltip from "$lib/components/reusable/WithTooltip.svelte";
  import { updateMetadata } from "$lib/seo";
  import { Label, Separator, Switch, Tabs } from "bits-ui";
  import { fly } from "svelte/transition";

  updateMetadata({ ogTitle: "LLM-Friendly Docs for HMR", ogDescription: "HMR library documentation in llms.txt format for AI assistants" });

  export let data: PageData;

  let content = "";
  let mounted = false;
  let loading = true;
  let viewMode: "raw" | "rendered" = "raw";
  let includeTests = false;
  let xml = false;

  $: url = `${$page.url.origin}/hmr/llms${includeTests ? "-full" : ""}${xml ? ".xml" : ".txt"}`;

  $: if (xml && viewMode === "rendered")
    viewMode = "raw";

  const getMounted = () => mounted; // no tracking

  $: {
    loading = true;
    browser && (!getMounted() ? data.html : fetch(url, { headers: { accept: xml ? "application/xml" : "text/markdown" } }).then(r => r.text())).then((text) => {
      content = text;
    }).catch((error) => {
      content = String(error);
    }).finally(() => {
      mounted = true;
      loading = false;
    });
  }

</script>

<div id="llms-page-root" class="m-4 w-[calc(100%-2rem)] col self-center 2xl:(m-14) lg:(m-10 max-w-4xl) md:(m-8 w-[calc(100%-4rem)] row) sm:(m-6 w-[calc(100%-3rem)]) xl:(m-12 max-w-5xl) <md:gap-1">

  <div class="mr-0 pl-100 pr-0 pt-100 -ml-100 -mt-100 lg:(mr-0 pb-10 -mb-10 -translate-x-[calc(0.3rem+2.5vw)]) md:(mr-8 bg-#121212 pb-8 -mb-8) 2xl:(pb-14 -mb-14) xl:(pb-12 -mb-12)">
    <div class="w-full col overflow-y-scroll text-sm md:(sticky top-8 h-[calc(100dvh-4rem)] w-17rem px-3 -ml-3) 2xl:(top-14 h-[calc(100dvh-7rem)]) lg:(top-8 h-[calc(100dvh-4rem)] w-21rem px-5 -ml-5) xl:(top-12 h-[calc(100dvh-6rem)]) <md:(mb-3 mt-1 rounded-md p-7 ring-1.2 ring-neutral-8 ring-inset) [&_p]:(text-xs text-neutral-5)">
      <div class="mb-3 col shrink-0 gap-1.5 text-xs">
        <div class="row items-center gap-1.5">
          <h1 class="text-base text-neutral-2 font-semibold">LLM-Friendly Docs ✨</h1>
          <WithTooltip tips="about llms.txt spec" let:builder>
            <a href="https://llmstxt.org/" target="_blank" class="" {...builder} use:builder.action>
              <div class="i-mdi-help-circle-outline mb-0.1 size-4 text-neutral-6 hover:text-neutral-3" />
            </a>
          </WithTooltip>
        </div>
        <p>
          Copy the HMR documentation in llm-friendly formats. Feed this to your LLM agents to enhance their understanding of the HMR library.
        </p>
      </div>

      <div class="col gap-0.7 text-neutral-4 [&>:where(button,a)]:(w-full row items-center gap-2 rounded-lg px-2 py-1.5 -ml-2) [&>:w\here(button,a):hover]:(bg-white/7 text-white filter-none) [&>:where(button,a):focus-visible]:(outline-none ring-1.2 ring-neutral-2 ring-inset) ![&>:where(button,a):active]:(bg-neutral-2 text-neutral-8 shadow-lg shadow-neutral-2/20)">
        <UseCopy text={url} let:handleClick>
          <button on:click={handleClick}>
            <div class="i-si-copy-alt-line size-4" />
            Copy URL
          </button>
        </UseCopy>
        <UseCopy text={content} let:handleClick>
          <button on:click={handleClick}>
            <div class="i-si-copy-alt-fill size-4" />
            Copy Content
          </button>
        </UseCopy>
      </div>

      <Separator.Root class="h-3vh max-h-8 min-h-5" />

      <div class="mb-2 col shrink-0 gap-1.5 text-xs">
        <h3 class="text-sm text-neutral-2 font-semibold">Display Mode</h3>
        <p>
          Choose how to display the markdown content.
        </p>
      </div>

      <Tabs.Root bind:value={viewMode}>
        <Tabs.List class="grid cols-2 w-full gap-0.7 rounded-lg bg-white/2 p-0.5 [&>*]:(row items-center justify-center gap-1 rounded-md px-2 py-1.5 text-xs text-neutral-4)">
          <Tabs.Trigger value="rendered" disabled={xml} class="data-[disabled]:(cursor-not-allowed opacity-50) hover:(bg-white/7 text-neutral-1) focus-visible:(outline-none ring-1.2 ring-neutral-2 ring-inset) !data-[state=active]:(bg-neutral-2 text-neutral-7)">
            <div class="i-mdi-file-document size-4 -translate-y-0.21" />
            Rendered
          </Tabs.Trigger>
          <Tabs.Trigger value="raw" class="hover:(bg-white/7 text-neutral-1) focus-visible:(outline-none ring-1.2 ring-neutral-2 ring-inset) !data-[state=active]:(bg-neutral-2 text-neutral-7)">
            <div class="{xml ? "i-lucide-code-xml -translate-y-0.1" : "i-mdi-file-document-outline -translate-y-0.21"} size-4" />
            {xml ? "XML" : "Markdown"}
          </Tabs.Trigger>
        </Tabs.List>
      </Tabs.Root>

      <Separator.Root class="h-3vh max-h-8 min-h-5" />

      <div class="mb-2 col shrink-0 gap-1.5 text-xs">
        <h3 class="text-sm text-neutral-2 font-semibold">Content Options</h3>
        <p>
          Choose the format and whether to include code examples in the output.
        </p>
      </div>

      <div class="mt-1 col gap-1.5">
        <div class="col gap-1">
          <div class="row items-center justify-between">
            <Label.Root for="include-tests" class="text-sm text-neutral-3">
              Include unit tests
            </Label.Root>
            <Switch.Root bind:checked={includeTests} id="include-tests" class="peer h-4.5 w-9 inline-flex shrink-0 cursor-pointer items-center rounded-full bg-neutral-8 data-[state=checked]:bg-neutral-5 focus-visible:(outline-none ring-1.2 ring-neutral-2 ring-inset)">
              <Switch.Thumb class="pointer-events-none block size-3.5 shrink-0 rounded-full bg-white data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0.5" />
            </Switch.Root>
          </div>
          <p>
            When enabled, unit tests will be included in the documentation to provide usage examples. Token cost may increase a lot.
          </p>
        </div>

        <div class="col gap-1">
          <div class="row items-center justify-between">
            <Label.Root for="format-toggle" class="text-sm text-neutral-3">
              Output in XML
            </Label.Root>
            <Switch.Root bind:checked={xml} id="format-toggle" class="peer h-4.5 w-9 inline-flex shrink-0 cursor-pointer items-center rounded-full bg-neutral-8 data-[state=checked]:bg-neutral-5 focus-visible:(outline-none ring-1.2 ring-neutral-2 ring-inset)">
              <Switch.Thumb class="pointer-events-none block size-3.5 shrink-0 rounded-full bg-white data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0.5" />
            </Switch.Root>
          </div>
          <p>
            Some LLMs may prefer XML format for better understanding.
          </p>
        </div>
      </div>

      <Separator.Root class="h-3vh max-h-8 min-h-5" />

      <div class="mb-2 col shrink-0 gap-1.5 text-xs">
        <h3 class="text-sm text-neutral-2 font-semibold">About llms.txt</h3>
        <p>
          llms.txt provides LLM-friendly documentation in a structured markdown format.
          It helps AI assistants quickly understand projects by curating essential information
          and links to detailed resources.
        </p>
        <div class="space-y-1">
          <a href="https://llmstxt.org/" target="_blank" class="row items-center gap-1 text-xs text-neutral-5 hover:text-neutral-2">
            <div class="i-ic-round-subdirectory-arrow-right size-3.5" />
            <span>Official specification</span>
          </a>
        </div>
      </div>

      <Separator.Root class="invisible min-h-5 grow" />

      <nav class="[&>a]:before:i-material-symbols-arrow-insert-rounded col gap-3 [&>a]:(row items-center gap-1.5 text-sm text-neutral-4 before:content-['']) [&>a:hover]:text-white">
        <a href="/hmr/mcp" class="before:!i-octicon-mcp-24">
          MCP server
        </a>
        <a href="/hmr">
          Back
        </a>
      </nav>
    </div>
  </div>

  {#key content}
    {#if !loading}
      <main transition:fly={{ y: 5 }} class="mt-1 max-w-full overflow-x-hidden" style:--un-prose-hr="#ffffff20">
        <WithMarkdown let:parse>
          {#if viewMode === "rendered"}
            <Router node={parse(content)} />
          {:else}
            <section class="text-sm [&_code_*]:!font-jb">
              <CodeBlock lang="markdown" code={content} />
            </section>
          {/if}
        </WithMarkdown>
      </main>
    {/if}
  {/key}

</div>

<style>
  :global(html):has(#llms-page-root) {
    scrollbar-gutter: stable;
  }
  section :global([style="color:#5D99A9"]) {
    font-style: italic;  /* blockquotes */
  }
</style>
