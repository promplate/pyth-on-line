<script lang="ts">
  import Intro from "#lib/components/Intro.svelte";
  import { canLogin, login } from "#lib/oauth.js";
  import { updateMetadata } from "#lib/seo.js";
  import { beforeNavigate, goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { toast } from "svelte-sonner";

  updateMetadata({ ogTitle: "Open GitHub Repositories", ogDescription: "Explore and interact with GitHub repositories as interactive Python workspaces in your browser." });

  let input = $state("");
  let mounted = $state(false);

  onMount(() => {
    mounted = true;
  });

  const valid = $derived(input.split("/").length === 2 && !input.endsWith("/") && !input.startsWith("/"));

  function openRepository(event: SubmitEvent) {
    event.preventDefault();
    goto(`/github/${input.split("/").map(encodeURIComponent).join("/")}`);
  }

  beforeNavigate(({ complete, to }) => {
    if (to?.route.id === "/(workspace)/github/[owner]/[repo]") {
      const { owner, repo } = to.params!;
      toast.promise(complete, { loading: `Fetching ${owner}/${repo}` });
    }
  });
</script>

<Intro title="Open a GitHub Repository">
  <a href="/github/promplate/pyth-on-line" style:--x="-5px" style:--delay="100ms">
    <div class="i-tabler-inner-shadow-bottom-right text-lg text-rose"></div>
    This site
  </a>
  <a href="/github/promplate/core" style:--x="5px" style:--delay="150ms">
    <div class="i-tabler-building-lighthouse text-lg text-yellow"></div>
    Our prompt engineering framework
  </a>
  <a href="/github/pyodide/micropip" style:--x="-5px" style:--delay="300ms">
    <div class="i-tabler-brand-python text-lg text-blue"></div>
    Pyodide's Micropip
  </a>
  <form action="/github" onsubmit={openRepository} style:--x="5px" style:--delay="500ms">
    <label class="contents">
      <div class={["i-tabler-brand-github text-lg text-zinc-4 transition-color", { "text-zinc-1": valid }]}></div>
      <input name="repo" aria-label="GitHub repository" required pattern="[^\/]+/[^\/]+" title="owner/repository" class={["w-50 bg-transparent outline-none placeholder:(text-inherit op-30)", { "animate-pulse": !input }]} placeholder="owner/repository" bind:value={input}>
    </label>
    {#if mounted && canLogin()}
      <button type="button" class="translate-x-1 rounded bg-zinc-2/12 p-1.5 transition-background-color hover:bg-zinc-2/20" onclick={login} title="Login to access your private repositories">
        <div class="i-lets-icons-sign-in-circle"></div>
      </button>
    {/if}
  </form>
</Intro>
