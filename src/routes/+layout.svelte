<script>
  import "@unocss/reset/tailwind.css";
  import "uno.css";
  import "@fontsource-variable/fira-code";
  import "misans-vf";

  import { dev } from "$app/environment";
  import { page } from "$app/stores";
  import * as env from "$env/static/public";
  import CmdK from "$lib/components/command/CmdK.svelte";
  import { Toaster } from "svelte-sonner";

  // @ts-ignore
  const headScripts = atob(env.PUBLIC_HEAD_SCRIPTS ?? "");
  // @ts-ignore
  const originTrialToken = env.PUBLIC_ORIGIN_TRIAL_TOKEN;

  const ogTitle = "Python Online";
  const ogImage = `${$page.url.origin.replace("http://sveltekit-prerender", "")}/og${$page.url.pathname}`;
  const ogDescription = "A simple online python console";
</script>

<svelte:head>
  {#if headScripts && !dev}
    {@html headScripts}
  {/if}
  {#if originTrialToken}
    <meta http-equiv="origin-trial" content={originTrialToken} />
  {/if}

  <title>{ogTitle}</title>
  <meta property="og:title" content={ogTitle} />
  <meta property="twitter:title" content={ogTitle} />

  <meta property="twitter:card" content="summary_large_image" />

  <meta property="og:image" content={ogImage} />
  <meta property="twitter:image" content={ogImage} />

  <meta property="description" content={ogDescription} />
  <meta property="og:description" content={ogDescription} />
  <meta property="twitter:description" content={ogDescription} />

  <meta name="theme-color" content="#171717" />
</svelte:head>

<Toaster theme="dark" toastOptions={{ class: "text-xs font-mono" }} />

<slot />

<CmdK />

<style>
  :global(html) {
    --uno: bg-neutral-9 text-white overflow-x-hidden font-sans;
  }

  :global(*)::selection {
    --uno: bg-white/15;
  }

  :global(body) {
    --uno: relative flex flex-col items-center items-stretch;
  }

  :global(body)::-webkit-scrollbar {
    --uno: bg-neutral-9 w-1 sm:w-1.5 md:w-2 lg:w-2.5 xl:w-3 2xl:w-3.5;
  }

  :global(body)::-webkit-scrollbar-thumb {
    --uno: rounded-l-sm bg-neutral-7/30 hover:bg-neutral-7/70;
  }

  :global(body *)::-webkit-scrollbar {
    --uno: hidden;
  }
</style>
