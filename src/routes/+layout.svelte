<script>
  import "@unocss/reset/tailwind.css";
  import "uno.css";

  import { dev } from "$app/environment";
  import { page } from "$app/stores";
  import * as env from "$env/static/public";
  import { Toaster } from "svelte-sonner";

  const headScripts = atob(env.PUBLIC_HEAD_SCRIPTS ?? "");

  const ogTitle = "Python Online";
  const ogImage = `${$page.url.origin}/og${$page.url.pathname}`;
  const ogDescription = "A simple online python console";
</script>

<svelte:head>
  {#if headScripts && !dev}
    {@html headScripts}
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
</svelte:head>

<Toaster theme="dark" toastOptions={{ class: "text-xs font-mono" }} />

<slot />

<style>
  :global(html) {
    --uno: bg-neutral-9 text-white flex flex-col items-center overflow-x-hidden;
  }

  :global(*)::selection {
    --uno: bg-white/15;
  }

  :global(body)::-webkit-scrollbar {
    --uno: bg-neutral-9 w-1 sm:w-1.5 md:w-2 lg:w-2.5 xl:w-3 2xl:w-3.5;
  }

  :global(body)::-webkit-scrollbar-thumb {
    --uno: bg-neutral-7/30 hover:bg-neutral-7/70 rounded-l-sm;
  }

  :global(body *)::-webkit-scrollbar {
    --uno: hidden;
  }
</style>
