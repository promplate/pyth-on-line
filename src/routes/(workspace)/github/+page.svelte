<script lang="ts">
  import { beforeNavigate } from "$app/navigation";
  import Intro from "$lib/components/Intro.svelte";
  import { toast } from "svelte-sonner";
  import { fly } from "svelte/transition";

  let input = "";
  let ref: HTMLInputElement;

  $: valid = input.split("/").length === 2 && !input.endsWith("/") && !input.startsWith("/");

  beforeNavigate(({ complete, to }) => {
    if (to?.route.id === "/(workspace)/github/[owner]/[repo]") {
      const { owner, repo } = to.params!;
      toast.promise(complete, { loading: `Fetching ${owner}/${repo}` });
    }
  });
</script>

{#await Promise.resolve() then}
  <Intro title="打开一个 GitHub 仓库为工作区">
    <a href="github/promplate/pyth-on-line" in:fly|global={{ duration: 500, x: -5, delay: 100 }}>
      <div class="i-tabler-inner-shadow-bottom-right text-lg text-rose" />
      本项目
    </a>
    <a href="github/promplate/core" in:fly|global={{ duration: 500, x: 5, delay: 150 }}>
      <div class="i-tabler-building-lighthouse text-lg text-yellow" />
      我们的提示工程框架
    </a>
    <a href="github/pyodide/micropip" in:fly|global={{ duration: 500, x: -5, delay: 300 }}>
      <div class="i-tabler-brand-python text-lg text-blue" />
      pyodide/micropip
    </a>
    <a href="github/{input}" class="w-fit" class:cursor-text={!valid} on:click={e => !valid && ([e.preventDefault(), ref.focus()])} in:fly|global={{ duration: 500, x: 5, delay: 500 }}>
      <div class="i-tabler-brand-github text-lg text-gray-4 transition-color" class:text-gray-1={valid} />
      <input class="w-50 bg-transparent outline-none placeholder:(text-inherit op-30)" class:animate-pulse={!input} placeholder="Your GitHub repo" bind:this={ref} on:click|preventDefault={() => { ref.focus(); }} bind:value={input} on:keydown={e => e.key === "Enter" && ref.parentElement?.click()}>
    </a>
  </Intro>
{/await}
