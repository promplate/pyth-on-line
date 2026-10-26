<script lang="ts">
  import type { LayoutProps } from "./$types";

  import "@unocss/reset/tailwind.css";
  import "uno.css";
  import "@fontsource-variable/fira-code";
  import "@fontsource-variable/inter";

  import { onNavigate } from "$app/navigation";
  import CmdK from "$lib/components/command/CmdK.svelte";
  import Head from "$lib/components/Head.svelte";
  import { initMetadata, resetMetadata } from "$lib/seo";
  import { Toaster } from "svelte-sonner";

  const { children }: LayoutProps = $props();

  const metadata = initMetadata();
  onNavigate(() => resetMetadata(metadata));
</script>

<Toaster theme="dark" toastOptions={{ class: "text-xs font-mono" }} />

{@render children()}

<!-- Svelte hoists svelte:head; a child component lets SSR read metadata after page setup. -->
<Head {metadata} />

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
