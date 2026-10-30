<script lang="ts">
  import type { Metadata } from "#lib/metadata.svelte.js";

  import { dev } from "$app/env";
  import * as env from "$app/env/public";
  import { page } from "$app/state";

  const { metadata }: { metadata: Metadata } = $props();

  // @ts-ignore
  const headScripts = atob(env.PUBLIC_HEAD_SCRIPTS ?? "");
  // @ts-ignore
  const originTrialToken = env.PUBLIC_ORIGIN_TRIAL_TOKEN;

  const ogImage = $derived(`${page.url.origin === "http://sveltekit-prerender" ? __PRERENDER_ORIGIN__ : page.url.origin}/og${page.url.pathname}`);
</script>

<svelte:head>
  {#if headScripts && !dev}
    {@html headScripts}
  {/if}
  {#if originTrialToken}
    <meta http-equiv={"origin-trial" as any} content={originTrialToken} />
  {/if}

  <title>{metadata.ogTitle}</title>
  <meta property="og:title" content={metadata.ogTitle} />
  <meta property="twitter:title" content={metadata.ogTitle} />

  <meta property="twitter:card" content="summary_large_image" />

  <meta property="og:image" content={ogImage} />
  <meta property="twitter:image" content={ogImage} />

  <meta name="description" content={metadata.ogDescription} />
  <meta property="og:description" content={metadata.ogDescription} />
  <meta property="twitter:description" content={metadata.ogDescription} />

  <meta name="theme-color" content="#171717" />
</svelte:head>
