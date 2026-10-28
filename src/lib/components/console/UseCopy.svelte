<script lang="ts">
  import type { Snippet } from "svelte";

  import { toastMarkdown } from "#lib/utils/toast.js";

  const { text, children }: { text: string; children: Snippet<[() => Promise<void>]> } = $props();

  async function handleClick() {
    const source = text.trimEnd();
    try {
      await navigator.clipboard.writeText(source);
    }
    catch {
      toastMarkdown("failed to copy to clipboard", "error");
      return;
    }
    const n = source.split("\n").length;
    toastMarkdown(`successfully copied \`${n}\` ${n === 1 ? "line" : "lines"} to clipboard`);
  }
</script>

{@render children(handleClick)}
