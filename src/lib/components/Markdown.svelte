<script lang="ts">
  import "../md.css";

  export let html: string;
</script>

<article class="min-w-full text-sm text-neutral-2 font-sans prose [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
  {@html html}
</article>
