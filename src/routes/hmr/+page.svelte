<script lang="ts">
  import FancyButton from "./FancyButton.svelte";
  import SparklesText from "./SparklesText.svelte";
  import { navigating } from "$app/stores";
  import { updateMetadata } from "$lib/seo";
  import { onMount } from "svelte";
  import { get } from "svelte/store";

  updateMetadata({
    ogTitle: "HMR - Hot Module Reload for Python",
    ogDescription: "Next-generation hot module replacement for Python development",
  });

  let highlighted = !get(navigating)?.from;
  highlighted && onMount(() => setTimeout(() => highlighted = false, 500));
</script>

<div class="grid h-100dvh place-items-center">
  <div class="m-3 lg:m-9 md:m-7 sm:m-5">

    <div class="relative mx-auto">
      <div class="mx-auto mb-8 max-w-7xl p-4 lg:px-8 sm:px-6">
        <div class="relative text-center">
          <div class="mb-6">
            <h2 class="mb-4 inline-flex translate-y-0.1 items-center gap-1.5 rounded-lg px-3 py-2 text-base text-rose ring-(1.2 rose/20) <md:(col py-4)">
              <div class="i-mdi-alert-outline size-4 <md:size-5 -translate-y-0.2" />
              <span>The docs is still under construction, but LLM-friendly docs are available now!</span>
            </h2>
          </div>
          <div class="mx-auto max-w-3xl">
            <h1>
              <SparklesText text="Hot Module Reload" class="text-3xl text-white font-bold tracking-tight md:text-5xl sm:text-4xl" />
            </h1>
            <h2 class="mx-auto mt-4 max-w-2xl text-balance text-base text-neutral leading-7">
              On-demand hot reloading. Only Python can do. Powered by fine-grained push-pull reactivity.
            </h2>
            <h3 class="mt-7 flex items-center justify-center">
              <FancyButton href="/hmr/llms" text="use llms.txt" {highlighted} />
            </h3>
          </div>
        </div>
      </div>
    </div>

    <div class="mb-10">
      <div class="mx-auto max-w-4xl px-4 lg:px-8 sm:px-6">
        <div class="grid grid-cols-1 mx-auto max-w-4xl gap-3 md:grid-cols-2 sm:gap-4">

          <a href="/hmr/mcp" class="group rounded-xl bg-white/2 p-3 ring-(1.2 transparent) md:col-span-2 sm:p-4 focus-visible:(outline-none ring-1.2 ring-neutral-2) hover:ring-neutral-6">
            <div class="flex items-center gap-2 sm:gap-3">
              <div class="h-8 w-8 flex items-center justify-center rounded-lg bg-white/10">
                <div class="i-octicon-mcp-24 size-4 text-neutral" />
              </div>
              <div class="flex-1 text-left">
                <h3 class="text-sm text-neutral-2 font-semibold sm:text-base">Docs as an MCP Server</h3>
                <p class="text-xs text-neutral sm:text-sm">For AI agents like Cursor, Claude Code, etc</p>
              </div>
              <div class="i-lucide-arrow-right size-4 text-neutral-5 group-hover:-rotate-45" />
            </div>
          </a>

          <a href="/hmr/llms" class="group rounded-xl bg-white/2 p-3 ring-(1.2 transparent) sm:p-4 focus-visible:(outline-none ring-1.2 ring-neutral-2) hover:ring-neutral-6">
            <div class="flex items-center gap-2 sm:gap-3">
              <div class="h-8 w-8 flex items-center justify-center rounded-lg bg-white/10">
                <div class="i-mdi-file-document-outline size-4 text-neutral" />
              </div>
              <div class="flex-1 text-left">
                <h3 class="text-sm text-neutral-2 font-semibold sm:text-base">llms.txt</h3>
                <p class="text-xs text-neutral sm:text-sm">Customizable LLM-friendly documentation</p>
              </div>
              <div class="i-lucide-arrow-right size-4 text-neutral-5 group-hover:-rotate-45" />
            </div>
          </a>

          <a href="https://pypi.org/project/hmr/" target="_blank" class="group rounded-xl bg-white/2 p-3 ring-(1.2 transparent) sm:p-4 focus-visible:(outline-none ring-1.2 ring-neutral-2) hover:ring-neutral-6">
            <div class="flex items-center gap-2 sm:gap-3">
              <div class="h-8 w-8 flex items-center justify-center rounded-lg bg-white/10">
                <div class="i-mynaui-package size-4 text-neutral" />
              </div>
              <div class="flex-1 text-left">
                <h3 class="text-sm text-neutral-2 font-semibold sm:text-base">PyPI</h3>
                <p class="text-xs text-neutral sm:text-sm">Install and get started</p>
              </div>
              <div class="i-lucide-arrow-right size-4 text-neutral-5 group-hover:-rotate-45" />
            </div>
          </a>

          <a href="https://github.com/promplate/hmr" target="_blank" class="group rounded-xl bg-white/2 p-3 ring-(1.2 transparent) sm:p-4 focus-visible:(outline-none ring-1.2 ring-neutral-2) hover:ring-neutral-6">
            <div class="flex items-center gap-2 sm:gap-3">
              <div class="h-8 w-8 flex items-center justify-center rounded-lg bg-white/10">
                <div class="i-mdi-github size-4 text-neutral" />
              </div>
              <div class="flex-1 text-left">
                <h3 class="text-sm text-neutral-2 font-semibold sm:text-base">Issue Tracker</h3>
                <p class="text-xs text-neutral sm:text-sm">Report bugs and request features</p>
              </div>
              <div class="i-lucide-arrow-right size-4 text-neutral-5 group-hover:-rotate-45" />
            </div>
          </a>

          <a href="https://github.com/promplate/pyth-on-line/tree/main/packages/hmr" target="_blank" class="group rounded-xl bg-white/2 p-3 ring-(1.2 transparent) sm:p-4 focus-visible:(outline-none ring-1.2 ring-neutral-2) hover:ring-neutral-6">
            <div class="flex items-center gap-2 sm:gap-3">
              <div class="h-8 w-8 flex items-center justify-center rounded-lg bg-white/10">
                <div class="i-mdi-github size-4 text-neutral" />
              </div>
              <div class="flex-1 text-left">
                <h3 class="text-sm text-neutral-2 font-semibold sm:text-base">Source Code</h3>
                <p class="text-xs text-neutral sm:text-sm">Explore the implementation</p>
              </div>
              <div class="i-lucide-arrow-right size-4 text-neutral-5 group-hover:-rotate-45" />
            </div>
          </a>

        </div>
      </div>
    </div>
  </div>

</div>
