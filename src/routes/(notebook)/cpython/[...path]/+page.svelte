<script lang="ts">
  import type { SvelteComponent } from "svelte";
  import type { PageData } from "./$types";

  import { onMount } from "svelte";

  export let data: PageData;

  let Client: (new (...args: any[]) => SvelteComponent) | null = null;

  onMount(async () => {
    // Keep the server chunk tiny; load the heavy notebook renderer in the browser only.
    Client = (await import("./CpythonClient.svelte")).default;
  });
</script>

{#if Client}
  <svelte:component this={Client} {data} />
{:else}
  <div class="grid h-50vh w-full place-items-center rounded-md bg-white/3">
    <div class="i-svg-spinners-90-ring-with-bg op-50" />
  </div>
{/if}
