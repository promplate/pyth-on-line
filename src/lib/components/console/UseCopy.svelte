<script lang="ts">
  import { toastMarkdown } from "$lib/utils/toast";

  export let text: string;

  async function handleClick() {
    text = text.trimEnd();
    navigator.clipboard.writeText(text);
    const n = text.split("\n").length;
    toastMarkdown(`successfully copied \`${n}\` ${n === 1 ? "line" : "lines"} to clipboard`);
  }
</script>

<slot {handleClick} />
