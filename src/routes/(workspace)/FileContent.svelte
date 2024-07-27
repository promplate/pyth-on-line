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

{#key content}
  <Editor lang={getLanguage(lang)} showLineNum source={content} />
{/key}
