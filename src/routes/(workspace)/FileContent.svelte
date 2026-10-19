<script lang="ts">
  import Editor from "$lib/components/Editor.svelte";

  let { content = $bindable(), lang, onsave }: { content: string; lang: string; onsave?: (source: string) => void } = $props();

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

<Editor {onsave} lang={getLanguage(lang)} showLineNum bind:source={content} />
