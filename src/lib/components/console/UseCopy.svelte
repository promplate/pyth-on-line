<script lang="ts">
  import type { Snippet } from "svelte";

  import { toastMarkdown } from "$lib/utils/toast";

  const { text, children }: { text: string; children: Snippet<[() => Promise<void>]> } = $props();

  async function handleClick() {
    const source = text.trimEnd();
    navigator.clipboard.writeText(source);
    const n = source.split("\n").length;
    toastMarkdown(`successfully copied \`${n}\` ${n === 1 ? "line" : "lines"} to clipboard`);
  }
</script>

{@render children(handleClick)}
