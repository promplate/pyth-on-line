<script lang="ts">
  import type { MetadataContext } from "$lib/contexts";

  import "@unocss/reset/tailwind.css";
  import "uno.css";
  import "@fontsource-variable/fira-code";
  import "@fontsource-variable/inter";

  import { dev } from "$app/environment";
  import { page } from "$app/stores";
  import * as env from "$env/static/public";
  import CmdK from "$lib/components/command/CmdK.svelte";
  import { METADATA_CONTEXT_KEY } from "$lib/contexts";
  import { getMetadata, metadataStore, updateMetadata } from "$lib/metadata";
  import { setContext } from "svelte";
  import { Toaster } from "svelte-sonner";

  // @ts-ignore
  const headScripts = atob(env.PUBLIC_HEAD_SCRIPTS ?? "");
  // @ts-ignore
  const originTrialToken = env.PUBLIC_ORIGIN_TRIAL_TOKEN;

  // Set up context for child components to update metadata
  const metadataContext: MetadataContext = {
    updateMetadata,
  };
  setContext(METADATA_CONTEXT_KEY, metadataContext);

  // Reactive metadata based on current page URL
  $: currentUrl = $page.url.pathname;
  $: currentMetadata = getMetadata(currentUrl, $metadataStore);
  $: ogTitle = currentMetadata.title ?? "Python Online";
  $: ogDescription = currentMetadata.description ?? "A simple online python console";
  $: ogImage = currentMetadata.image ?? `${$page.url.origin.replace("http://sveltekit-prerender", "")}/og${$page.url.pathname}`;
  $: ogType = currentMetadata.type ?? "website";
  $: twitterCard = currentMetadata.twitterCard ?? "summary_large_image";
  $: themeColor = currentMetadata.themeColor ?? "#171717";
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

  <meta property="og:type" content={ogType} />
  <meta property="twitter:card" content={twitterCard} />

  <meta property="og:image" content={ogImage} />
  <meta property="twitter:image" content={ogImage} />

  <meta name="description" content={ogDescription} />
  <meta property="og:description" content={ogDescription} />
  <meta property="twitter:description" content={ogDescription} />

  <meta name="theme-color" content={themeColor} />

  {#if currentMetadata.url}
    <meta property="og:url" content={currentMetadata.url} />
    <link rel="canonical" href={currentMetadata.url} />
  {/if}

  {#if currentMetadata.siteName}
    <meta property="og:site_name" content={currentMetadata.siteName} />
  {/if}
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
