<script lang="ts">
  import Editor from "$lib/components/Editor.svelte";

  interface Props {
    content: string;
    lang: string;
  }

  let { content = $bindable(), lang }: Props = $props();

  function getLanguage(ext: string) {
    switch (ext) {
      case "j2":
        return "jinja";
      case "pyi":
        return "python";
      default:
        return ext;
    }
  }
</script>

<Editor on:save lang={getLanguage(lang)} showLineNum bind:source={content} />
