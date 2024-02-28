<script lang="ts">
  import Markdown from "../Markdown.svelte";
  import { md } from "$lib/markdown";
  import { toast } from "svelte-sonner";

  export let text: string;

  async function handleClick() {
    text = text.trimEnd();

    const n = text.split("\n").length;

    const html = await md`successfully copied \`${n}\` ${n === 1 ? "line" : "lines"} to clipboard`;

    toast.success(Markdown, { componentProps: { html } });
    navigator.clipboard.writeText(text);
  }
</script>

<button on:click={handleClick} class="i-icon-park-twotone-copy" />
