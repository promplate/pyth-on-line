<script module lang="ts">
  import "../../md.css";

  import { fromMarkdown } from "mdast-util-from-markdown";
  import { gfmFromMarkdown } from "mdast-util-gfm";
  import { gfm } from "micromark-extension-gfm";
  import remarkInlineLinks from "remark-inline-links";

  const inlineLinks = remarkInlineLinks();

  function parse(text: string) {
    const root = fromMarkdown(text, {
      extensions: [gfm()],
      mdastExtensions: [gfmFromMarkdown()],
    });
    inlineLinks(root);
    return root;
  }
</script>

<script lang="ts">
  import type { Snippet } from "svelte";

  const { children }: { children?: Snippet<[typeof parse]> } = $props();
</script>

<article class="max-w-full text-sm text-neutral-2 font-sans prose [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
  {@render children?.(parse)}
</article>
