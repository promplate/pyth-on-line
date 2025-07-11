<script lang="ts">
  import { page } from "$app/stores";
</script>

<div class="grid h-95vh place-items-center">
  <div class="max-w-7xl flex flex-col gap-6">
    <h1 class="text-5xl font-210 tracking-widest">{$page.status}</h1>
    <h2 class="min-w-sm overflow-x-scroll whitespace-pre rounded bg-white/5 p-5 font-mono -mx-1">{$page.error?.message}</h2>
  </div>
</div>
