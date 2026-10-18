<script lang="ts">
  import { page as pageState } from "$app/state";
  import { toStore } from "svelte/store";

  // Bridge Kit state to the existing store syntax without losing navigation updates.
  const page = toStore(() => ({ ...pageState }));
</script>

<div class="grid h-95vh place-items-center">
  <div class="max-w-7xl flex flex-col gap-6">
    <h1 class="text-5xl font-200 tracking-widest">{$page.status}</h1>
    <h2 class="min-w-sm overflow-x-scroll whitespace-pre rounded bg-white/5 p-5 font-mono -mx-1">{$page.error?.message}</h2>
  </div>
</div>
