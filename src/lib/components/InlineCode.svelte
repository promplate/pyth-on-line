<script lang="ts">
  import { highlight } from "../highlight";

  export let lang = "python";
  export let text: string;
</script>

<div tabindex="-1" class="contents [&>pre]:(inline whitespace-pre-wrap) [&_code>span]:min-h-[calc(2em-8px)] [&_code]:(flex flex-col gap-0.2em) [&_span]:font-mono ![&>pre]:bg-transparent">
  {#await highlight(lang, text)}
    {text}
  {:then html}
    {@html html}
  {/await}
</div>
