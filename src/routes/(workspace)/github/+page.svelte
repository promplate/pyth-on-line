<script lang="ts">
  import { beforeNavigate } from "$app/navigation";
  import Intro from "$lib/components/Intro.svelte";
  import { canLogin, login } from "$lib/oauth";
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
    <a href="/github/promplate/pyth-on-line" in:fly|global={{ duration: 500, x: -5, delay: 100 }}>
      <div class="i-tabler-inner-shadow-bottom-right text-lg text-rose" />
      本项目
    </a>
    <a href="/github/promplate/core" in:fly|global={{ duration: 500, x: 5, delay: 150 }}>
      <div class="i-tabler-building-lighthouse text-lg text-yellow" />
      我们的提示工程框架
    </a>
    <a href="/github/pyodide/micropip" in:fly|global={{ duration: 500, x: -5, delay: 300 }}>
      <div class="i-tabler-brand-python text-lg text-blue" />
      pyodide/micropip
    </a>
    <a href="/github/{input}" class="w-fit" class:cursor-text={!valid} on:click={e => !valid && ([e.preventDefault(), ref.focus()])} in:fly|global={{ duration: 500, x: 5, delay: 500 }}>
      <div class="i-tabler-brand-github text-lg text-zinc-4 transition-color" class:text-zinc-1={valid} />
      <input class="w-50 bg-transparent outline-none placeholder:(text-inherit op-30)" class:animate-pulse={!input} placeholder="你的 GitHub 仓库" bind:this={ref} on:click|preventDefault={() => { ref.focus(); }} bind:value={input} on:keydown={e => e.key === "Enter" && ref.parentElement?.click()}>
      {#if $canLogin}
        <button class="translate-x-1 rounded bg-zinc-2/12 p-1.5 transition-background-color hover:bg-zinc-2/20" on:click={login} title="登录以访问私有仓库">
          <div class="i-lets-icons-sign-in-circle" />
        </button>
      {/if}
    </a>
  </Intro>
{/await}
