<script lang="ts">
  import { page } from "$app/stores";
  import { show as showMenu } from "$lib/components/command/CmdK.svelte";
  import FeatureCard from "$lib/components/FeatureCard.svelte";
  import Hero from "$lib/components/Hero.svelte";
  import { useMetadata } from "$lib/useMetadata";
  import { onMount } from "svelte";

  const { updateMetadata } = useMetadata();

  onMount(() => {
    // Set specific metadata for the home page
    updateMetadata($page.url.pathname, {
      title: "Python Online - Interactive Python in Your Browser",
      description: "Run Python code directly in your browser with our interactive online Python environment. No installation required - powered by Pyodide.",
      type: "website",
      siteName: "Python Online",
    });
  });
</script>

<div class="grid min-h-screen place-items-center">
  <div class="b-(1 white/10) bg-white/2">
    <div class="m-5 max-h-3xl w-auto flex flex-col justify-between gap-4 lg:m-15 md:m-11 sm:m-8">
      <div class="relative min-h-sm w-full self-center lg:max-w-3xl">
        <Hero />
      </div>
      <div class="flex flex-row flex-wrap gap-3 sm:(max-w-3xl self-center)">
        <FeatureCard icon="i-lucide-folder-dot" href="/playground" title="Open a playground" description="Open an isolated workspace of this site's python sources" />
        <FeatureCard icon="i-solar-command-bold-duotone" on:click={() => $showMenu = true} title="Try the shortcut menu" description="Press Ctrl/Cmd + K to open it" />
        <FeatureCard icon="i-mdi-github-face" href="/github" title="Clone a GitHub repo" description="Open an isolated workspace from a specified GitHub repository" />
        <FeatureCard icon="i-ph-terminal-window-duotone" href="/console" title="Start an immersive console" description="Run Python 3.12 in an interactive console directly in your browser without installation" />
        <FeatureCard icon="i-hugeicons-hand-pointing-right-01" href="/about" title="Take a quick tour" description="Start a dedicated jupyter-like notebook to have a glance of our features" />
        <FeatureCard icon="i-hugeicons-package-search" href="/pypi" title="Explore PyPI" description="Search packages on PyPI" />
      </div>
    </div>
  </div>
</div>
