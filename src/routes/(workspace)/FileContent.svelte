<script lang="ts">
  import Editor from "$lib/components/Editor.svelte";

  export let content: string;
  export let lang: string;

  function getLanguage(ext: string) {
    switch (ext) {
      case "j2":
        return "jinja";
      default:
        return ext;
    }
  }
</script>

<Editor on:save lang={getLanguage(lang)} showLineNum bind:source={content} />
