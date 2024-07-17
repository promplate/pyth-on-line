<script lang="ts">
  export let href: string;
  export let icon: string;
  export let title: string;
  export let description: string;
</script>

<a {href} class="max-h-40 w-full rounded-sm bg-white/2 p-6 ring-transparent transition hover:bg-white/5 hover:ring-(1.2 white/50 inset)">
  <div class="flex flex-col gap-3">
    <div class="flex flex-row items-center gap-2">
      <div class="{icon} text-2xl" />
      <h3 class="text-lg">{title}</h3>
    </div>
    <div class="text-sm op-70">{description}</div>
  </div>
</a>
