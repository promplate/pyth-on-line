<script module lang="ts">
  import "../../md.css";

  import GithubSlugger from "github-slugger";
  import { fromMarkdown } from "mdast-util-from-markdown";
  import { gfmFromMarkdown } from "mdast-util-gfm";
  import { toString } from "mdast-util-to-string";
  import { gfm } from "micromark-extension-gfm";
  import { visit } from "unist-util-visit";

  function parse(text: string) {
    const root = fromMarkdown(text, {
      extensions: [gfm()],
      mdastExtensions: [gfmFromMarkdown()],
    });
    const slugger = new GithubSlugger();
    visit(root, "heading", (node) => {
      node.data = { hProperties: { id: slugger.slug(toString(node, { includeHtml: false })) } };
    });
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
