<script lang="ts">
  import Markdown from "../Markdown.svelte";
  import { toast } from "svelte-sonner";

  export let text: string;

  async function handleClick() {
    text = text.trimEnd();

    const n = text.split("\n").length;

    toast.success(Markdown, { componentProps: { text: `successfully copied \`${n}\` ${n === 1 ? "line" : "lines"} to clipboard` } });
    navigator.clipboard.writeText(text);
  }
</script>

<button on:click={handleClick} class="i-icon-park-twotone-copy" />
