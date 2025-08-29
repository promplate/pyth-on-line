<script lang="ts">
  import { toastMarkdown } from "$lib/utils/toast";

  interface Props {
    text: string;
    children?: import("svelte").Snippet<[any]>;
  }

  let { text = $bindable(), children }: Props = $props();

  async function handleClick() {
    text = text.trimEnd();
    navigator.clipboard.writeText(text);
    const n = text.split("\n").length;
    toastMarkdown(`successfully copied \`${n}\` ${n === 1 ? "line" : "lines"} to clipboard`);
  }
</script>

{@render children?.({ handleClick })}
