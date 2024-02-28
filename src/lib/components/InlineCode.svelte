<script lang="ts">
  import { highlight } from "../highlight";

  export let lang = "python";
  export let text: string;
</script>

<div tabindex="-1" class="contents [&>pre]:(inline whitespace-pre-wrap) [&_code>span]:min-h-1.4em [&_code]:(flex flex-col gap-0.7) [&_span]:font-mono ![&>pre]:bg-transparent">
  {#await highlight(lang, text)}
    {text}
  {:then html}
    {@html html}
  {/await}
</div>
