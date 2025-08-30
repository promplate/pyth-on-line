<script lang="ts">
  interface Props {
    children?: import("svelte").Snippet<[any]>;
  }

  const { children }: Props = $props();
</script>

<script module lang="ts">
  import "../../md.css";

  import { fromMarkdown } from "mdast-util-from-markdown";
  import { gfmFromMarkdown } from "mdast-util-gfm";
  import { gfm } from "micromark-extension-gfm";

  function parse(text: string) {
    return fromMarkdown(text, {
      extensions: [gfm()],
      mdastExtensions: [gfmFromMarkdown()],
    });
  }
</script>

<article class="max-w-full text-sm text-neutral-2 font-sans prose [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
  {@render children?.({ parse })}
</article>
