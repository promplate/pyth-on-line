<script lang="ts">
  import { show as showMenu } from "$lib/components/command/CmdK.svelte";
  import FeatureCard from "$lib/components/FeatureCard.svelte";
  import Hero from "$lib/components/Hero.svelte";
</script>

<div class="grid min-h-screen place-items-center">
  <div class="b-(1 white/10) bg-white/2">
    <div class="m-5 max-h-3xl w-auto flex flex-col justify-between gap-4 lg:m-15 md:m-11 sm:m-8">
      <div class="relative min-h-sm w-full self-center lg:max-w-3xl">
        <Hero />
      </div>
      <div class="flex flex-row flex-wrap gap-3 sm:(max-w-3xl self-center)">
        <FeatureCard icon="i-ph-terminal-window-duotone" href="/console" title="Python 控制台" description="打开一个沉浸式控制台" />
        <FeatureCard icon="i-hugeicons-hand-pointing-right-01" href="/about" title="自我介绍" description="功能简介" />
        <FeatureCard icon="i-solar-command-bold-duotone" on:click={() => $showMenu = true} title="试试快捷菜单" description="按 Ctrl/Cmd + K 打开" />
        <FeatureCard icon="i-hugeicons-package-search" href="/pypi" title="探索 PyPI" description="搜索 PyPI 上的包" />
        <FeatureCard icon="i-mdi-github-face" href="/github" title="打开一个 GitHub 仓库" description="从指定的 GitHub 仓库打开一个工作区" />
        <FeatureCard icon="i-lucide-folder-dot" href="/playground" title="看看本站源码" description="本站的 Python 代码" />
      </div>
    </div>
  </div>
</div>
