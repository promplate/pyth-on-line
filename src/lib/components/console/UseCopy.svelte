<script lang="ts">
  import { toast } from "svelte-sonner";

  export let text: string;

  async function handleClick() {
    text = text.trimEnd();
    navigator.clipboard.writeText(text);
    const n = text.split("\n").length;
    const { default: Markdown } = await import("../Markdown.svelte");
    toast.success(Markdown, { componentProps: { text: `successfully copied \`${n}\` ${n === 1 ? "line" : "lines"} to clipboard` } });
  }
</script>

<slot {handleClick} />
