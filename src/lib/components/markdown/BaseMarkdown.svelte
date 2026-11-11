<script module lang="ts">
  import type { Root } from "mdast";

  import GithubSlugger from "github-slugger";
  import { toString } from "mdast-util-to-string";
  import { visit } from "unist-util-visit";

  function withHeadingIds(root: Root) {
    const slugger = new GithubSlugger();
    visit(root, "heading", (node) => {
      node.data = { hProperties: { id: slugger.slug(toString(node, { includeHtml: false })) } };
    });
    return root;
  }
</script>

<script lang="ts">
  import WithMarkdown from "../reusable/WithMarkdown.svelte";
  import Router from "./Router.svelte";

  const { text, headingIds = false }: { text: string; headingIds?: boolean } = $props();
</script>

<WithMarkdown>
  {#snippet children(parse)}
    <Router node={headingIds ? withHeadingIds(parse(text)) : parse(text)} />
  {/snippet}
</WithMarkdown>
