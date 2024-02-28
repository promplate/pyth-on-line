<script lang="ts">
  export let html: string;
</script>

<article class="min-w-full text-sm prose [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
  {@html html}
</article>

<style>
  article :global(:where(h1, h2, h3, h4, h5, h6)) {
    --uno: font-bold \!text-base text-white m-0;
  }

  article :global(strong) {
    --uno: text-white font-bold;
  }

  article :global(pre) {
    --uno: leading-relaxed py-4 px-3;
  }

  article :global(pre code) {
    --uno: whitespace-pre bg-transparent translate-none;
  }

  article :global(code) {
    --uno: inline-block py-0.2 -my-0.2 mx-0.2 -translate-y-0.1em font-normal px-1 text-0.8em rounded bg-white/10 text-white before:content-none after:content-none whitespace-normal;
  }
</style>
