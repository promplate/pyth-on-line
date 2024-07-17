<script lang="ts">
  import FeatureCard from "$lib/components/FeatureCard.svelte";
  import Hero from "$lib/components/Hero.svelte";
</script>

<div class="grid min-h-screen place-items-center">
  <div class="b-(1 white/10) bg-white/2">
    <div class="m-5 max-h-3xl w-auto flex flex-col justify-between gap-4 lg:m-15 md:m-11 sm:m-8">
      <div class="relative min-h-sm w-full self-center lg:max-w-3xl">
        <Hero />
      </div>
      <div class="flex flex-col gap-4 lg:(max-w-3xl flex-row self-center)">
        <FeatureCard icon="i-ph-terminal-window-duotone" href="/console" title="Start an immersive console" description="Run Python 3.12 in an interactive console directly in your browser without installation" />
        <FeatureCard icon="i-carbon-logo-jupyter" href="." title="Start a jupyter-like notebook" description="Still under development" />
      </div>
    </div>
  </div>
</div>
