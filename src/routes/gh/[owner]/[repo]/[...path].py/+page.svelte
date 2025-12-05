<!-- eslint-disable unocss/order -->
<script lang="ts">
  import type { PageData } from "./$types";
  import type { Payload } from "./types";

  import "@fontsource-variable/jetbrains-mono/wght.css";

  import { page } from "$app/stores";
  import CodeBlock from "$lib/components/CodeBlock.svelte";
  import UseCopy from "$lib/components/console/UseCopy.svelte";
  import Router from "$lib/components/markdown/Router.svelte";
  import WithMarkdown from "$lib/components/reusable/WithMarkdown.svelte";
  import { fromNow } from "$lib/date";
  import { updateMetadata } from "$lib/seo";
  import { Avatar } from "bits-ui";
  import { fly } from "svelte/transition";

  export let data: PageData;
  const payload = data.payload as Payload;

  updateMetadata({ ogTitle: `${payload.owner}/${payload.repo} · ${payload.filePath}` });

  $: currentUrl = $page.url.href;
  $: runCommand = `uv run ${currentUrl}`;

  function getSourceLabel(type: string) {
    switch (type) {
      case "pep723":
        return "PEP 723 header";
      case "pyproject":
        return "pyproject.toml";
      default:
        return "none";
    }
  }

  $: sourceLabel = getSourceLabel(payload.dependencySource.type);

  const sourceLink = payload.dependencySource.path
    ? `https://github.com/${payload.owner}/${payload.repo}/blob/${payload.ref}/${payload.dependencySource.path}`
    : null;

  const pyprojectLinks = payload.pyprojectPaths.map(item => ({
    ...item,
    href: `https://github.com/${payload.owner}/${payload.repo}/blob/${payload.ref}/${item.path}`,
  }));

  const repoLink = `https://github.com/${payload.owner}/${payload.repo}`;
  const refLink = `${repoLink}/tree/${payload.ref}`;

  function parseDep(dep: string) {
    // PEP 508: package names contain letters, digits, hyphens, underscores, periods
    const match = dep.match(/^([a-z\d][-\w.]*[a-z\d]|[a-z\d])(.*)/i);
    if (!match)
      return { name: dep, version: "" };
    return { name: match[1], version: match[2].trim() };
  }
</script>

<div id="gh-py-root" class="m-4 w-[calc(100%-2rem)] col self-center 2xl:(m-14) lg:(m-10 max-w-4xl) md:(m-8 w-[calc(100%-4rem)] row) sm:(m-6 w-[calc(100%-3rem)]) xl:(m-12 max-w-5xl) <md:gap-1">

  <div class="mr-0 pl-100 pr-0 pt-100 -ml-100 -mt-100 lg:(mr-0 pb-10 -mb-10 -translate-x-[calc(0.3rem+2.5vw)]) md:(mr-8 bg-#121212 pb-8 -mb-8) 2xl:(pb-14 -mb-14) xl:(pb-12 -mb-12)">
    <aside class="w-full col gap-9 overflow-y-scroll text-sm md:(sticky top-8 h-[calc(100dvh-4rem)] w-17rem px-3 -ml-3) 2xl:(top-14 h-[calc(100dvh-7rem)]) lg:(top-8 h-[calc(100dvh-4rem)] w-21rem px-5 -ml-5) xl:(top-12 h-[calc(100dvh-6rem)]) <md:(mb-3 mt-1 rounded-md p-7 ring-1.2 ring-neutral-8 ring-inset) [&_p]:(text-xs text-neutral-5)">

      <section class="col gap-2 rounded-lg bg-white/2 p-3 ring-1 ring-white/5">
        <div class="row items-center justify-between">
          <span class="text-[0.68rem] text-neutral-5 tracking-wider uppercase">Repository</span>
          <a href={refLink} target="_blank" rel="noreferrer" class="max-w-30 row gap-0.5 overflow-hidden text-xs text-neutral-4 font-mono hover:text-white">
            <span class="op-40">@</span>
            <span class="overflow-hidden text-ellipsis ws-nowrap">{payload.ref}</span>
          </a>
        </div>
        {#if payload.repository.description}
          <WithMarkdown let:parse>
            <div class="[&_a:hover]:text-white [&>*_a]:text-neutral-3 [&>*>*]:text-neutral-5 first:[&_p]:mt-0 last:[&_p]:mb-0">
              <Router node={parse(payload.repository.description)} />
            </div>
          </WithMarkdown>
        {/if}
        <div class="mt-1 row flex-wrap gap-3 text-xs text-neutral-4">
          <a href="{repoLink}/stargazers" target="_blank" rel="noreferrer" class="row items-center gap-1 hover:text-white"><div class="i-mdi-star size-3.5 text-amber-4" /> {payload.repository.stargazers}</a>
          <a href="{repoLink}/forks" target="_blank" rel="noreferrer" class="row items-center gap-1 hover:text-white"><div class="i-mdi-source-fork size-3.5" /> {payload.repository.forks}</a>
          <a href="{repoLink}/watchers" target="_blank" rel="noreferrer" class="row items-center gap-1 hover:text-white"><div class="i-mdi-eye-outline size-3.5" /> {payload.repository.watchers}</a>
        </div>
        <div class="mt-2 col gap-1.5 text-xs text-neutral-5">
          <div class="row justify-between">
            <span>Created</span>
            <span class="text-neutral-4">{fromNow(payload.repository.createdAt)}</span>
          </div>
          <div class="row justify-between">
            <span>Last push</span>
            <a href="{repoLink}/commits" target="_blank" rel="noreferrer" class="text-neutral-4 hover:text-white">{fromNow(payload.repository.pushedAt)}</a>
          </div>
          {#if payload.repository.primaryLanguage}
            <div class="row justify-between">
              <span>Language</span>
              <span class="flex items-center gap-1.5"><span class="block size-2 rounded-1/2" style="background-color: {payload.repository.primaryLanguage.color}" />{payload.repository.primaryLanguage.name}</span>
            </div>
          {/if}
          {#if payload.repository.licenseInfo}
            <div class="row justify-between">
              <span>License</span>
              <a href="{repoLink}/blob/{payload.ref}/LICENSE" target="_blank" rel="noreferrer" class="text-neutral-4 hover:text-white">{payload.repository.licenseInfo.name}</a>
            </div>
          {/if}
          {#if payload.repository.isArchived}
            <div class="row items-center gap-1.5 rounded-md bg-amber-4/10 px-2 py-1 text-amber-3 ring-1 ring-amber-4/20">
              <div class="i-mdi-archive-outline size-3" />
              <span>Archived</span>
            </div>
          {/if}
        </div>
      </section>

      <section class="col gap-2">
        <div class="row items-center justify-between">
          <span class="text-[0.68rem] text-neutral-5 tracking-wider uppercase">Dependencies</span>
          <span class="text-xs text-neutral-5">{sourceLabel}</span>
        </div>
        {#if sourceLink}
          <a href={sourceLink} target="_blank" rel="noreferrer" class="text-sm text-neutral-4 -translate-y-1 hover:text-white">
            <span class="text-neutral-5">from</span>
            <code>{payload.dependencySource.path}</code>
          </a>
        {/if}
        {#if payload.dependencies.length}
          <ul class="col gap-2">
            {#each payload.dependencies as dep}
              {@const parsed = parseDep(dep)}
              <li class="row items-baseline gap-0.5 ws-nowrap b-l-(2 teal-3) bg-gradient-(from-teal-4/7 via-teal-4/1 to-transparent to-r) px-2 py-0.7 text-xs font-mono">
                <a href="/pypi/{parsed.name}" class="text-teal-4 font-medium hover:(text-teal-2)">{parsed.name}</a>
                {#if parsed.version}
                  <span class="max-w-full overflow-hidden text-ellipsis text-teal-4/50">{parsed.version}</span>
                {/if}
              </li>
            {/each}
          </ul>
        {:else}
          <p class="text-xs text-neutral-6">No dependencies detected.</p>
        {/if}
      </section>

      {#if payload.repository.openIssuesCount > 0 || payload.repository.recentIssues.length > 0}
        <section class="col gap-2">
          <div class="row items-center justify-between">
            <span class="text-[0.68rem] text-neutral-5 tracking-wider uppercase">Latest Issues</span>
            <span class="text-xs text-neutral-5">{payload.repository.openIssuesCount} open</span>
          </div>
          {#if payload.repository.recentIssues.length > 0}
            <ul class="col gap-1.5">
              {#each payload.repository.recentIssues as issue}
                <li>
                  <a href={issue.url} target="_blank" rel="noreferrer" class="block truncate rounded-md px-2 py-1.5 text-xs text-neutral-4 ring-1 ring-white/5 hover:(bg-white/4 text-white)">
                    <span class="text-neutral-6">#{issue.number}</span>
                    <span class="font-medium">{issue.title}</span>
                  </a>
                </li>
              {/each}
            </ul>
          {/if}
        </section>
      {/if}

      {#if payload.repository.latestRelease}
        <section class="col gap-2">
          <div class="row items-center justify-between">
            <span class="text-[0.68rem] text-neutral-5 tracking-wider uppercase">Latest release</span>
            <span class="text-xs text-neutral-5 font-mono">{payload.repository.latestRelease.tagName}</span>
          </div>
          <a href="{repoLink}/releases/tag/{payload.repository.latestRelease.tagName}" target="_blank" rel="noreferrer" class="block rounded-md px-2 py-1.5 text-xs text-neutral-4 ring-1 ring-white/5 hover:(bg-white/4 text-white)">
            {#if payload.repository.latestRelease.name}
              <span class="font-medium">{payload.repository.latestRelease.name}</span>
            {/if}
            <div class="mt-1 text-[0.65rem] text-neutral-6">{fromNow(payload.repository.latestRelease.publishedAt)}</div>
          </a>
        </section>
      {/if}

      <section class="col gap-2">
        <span class="text-[0.68rem] text-neutral-5 tracking-wider uppercase">pyproject.toml</span>
        {#if pyprojectLinks.length > 0}
          <ul class="col gap-1">
            {#each pyprojectLinks as item}
              {#if item.exists}
                <li class="row items-center justify-between gap-2 rounded-md px-2 py-1.5 text-xs ring-1 {item.used ? "bg-teal-9/25 ring-teal-5/40" : "bg-black/30 ring-white/4"}">
                  <a href={item.href} target="_blank" rel="noreferrer" class="truncate font-mono {item.used ? "text-teal-3 hover:text-teal-2" : "text-neutral-4 hover:text-white"}">{item.path}</a>
                  <span class="shrink-0 text-[0.65rem] {item.used ? "text-teal-4" : "text-neutral-5"}">{item.used ? "used" : "found"}</span>
                </li>
              {/if}
            {/each}
          </ul>
        {:else}
          <p class="text-xs text-neutral-6">No pyproject.toml files found.</p>
        {/if}
      </section>

      <nav class="mt-auto col gap-2 pt-4 [&>*]:(row items-center gap-2)">
        <a href={repoLink} target="_blank" rel="noreferrer" class="row items-center gap-1.5 text-sm text-neutral-4 [&_span]:hover:text-white">
          <Avatar.Root class="size-5 shrink-0">
            <div class="grid size-full place-items-center overflow-hidden rounded-1/4 bg-neutral-1/5">
              <Avatar.Image src={payload.repository.ownerAvatarUrl} alt={`@${payload.repository.ownerLogin}`} />
              <Avatar.Fallback class="text-xs text-neutral-4/60">
                <div class="i-mdi-github size-3.5" />
              </Avatar.Fallback>
            </div>
          </Avatar.Root>
          <span class="overflow-hidden ws-nowrap">
            <span class="text-neutral-3">{payload.repository.ownerLogin}</span>
            <span class="op-50">/</span>
            {payload.repo}
          </span>
        </a>
      </nav>

    </aside>
  </div>

  <main class="w-full col gap-7 overflow-x-hidden">

    <section>
      <a href={payload.githubUrl} target="_blank" rel="noreferrer">
        <code class="font-mono">
          <span class="text-neutral-4">{payload.owner}/{payload.repo}/</span><h1 class="inline ws-nowrap text-neutral-2 font-semibold">{payload.filePath}</h1>
        </code>
      </a>
    </section>

    <section class="col gap-2 rounded-lg bg-#121212 p-4">
      <div class="text-[0.68rem] text-neutral-5 tracking-wider uppercase">
        Run with
        <a href="https://docs.astral.sh/uv/guides/scripts/" target="_blank" rel="noreferrer" class="underline underline-neutral-6 underline-offset-2 underline-dashed hover:text-neutral-2">
          uv
        </a>
      </div>
      <UseCopy text={runCommand} let:handleClick>
        <button class="max-w-full w-fit row items-center gap-2 rounded-lg bg-white/4 px-2.5 py-1.5 text-sm text-neutral-2 ring-1 ring-white/7 hover:bg-white/6" on:click={handleClick}>
          <div class="i-si-copy-alt-line size-4" />
          <code class="max-w-full overflow-hidden text-ellipsis ws-nowrap text-xs text-neutral-3 font-jb">{runCommand}</code>
        </button>
      </UseCopy>
    </section>

    <section in:fly={{ y: 2 }} class="col gap-3">
      <div class="row items-center justify-between">
        <div class="col gap-1">
          <h2 class="text-sm text-neutral-2 font-semibold">Served content</h2>
          <p class="text-xs text-neutral-5">Includes injected PEP 723 header when applicable.</p>
        </div>
        <div class="row items-center gap-3">
          <span class="text-xs text-neutral-5">Last changed {fromNow(payload.repository.fileLastUpdatedAt)}</span>
          <UseCopy text={payload.content} let:handleClick>
            <button class="row items-center gap-1.5 rounded-md bg-white/7 px-2.5 py-1.5 text-xs text-neutral-3 ring-1 ring-white/10 hover:bg-white/10" on:click={handleClick}>
              <div class="i-si-copy-alt-line size-3.5" />
              Copy
            </button>
          </UseCopy>
        </div>
      </div>
      <div class="text-sm [&_pre]:p-4 [&_code_*]:!font-jb">
        <CodeBlock code={payload.content} lang="python" />
      </div>
    </section>

  </main>

</div>

<style>
  :global(html):has(#gh-py-root) {
    scrollbar-gutter: stable;
  }
  button {
    --uno: outline-none focus-visible:ring-(1.2 neutral-5 inset);
  }
</style>
