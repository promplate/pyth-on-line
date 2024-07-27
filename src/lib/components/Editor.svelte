<script context="module">
  let firstLoad = true;
</script>

<script lang="ts">
  import type monaco from "monaco-editor-core";

  import { shikiToMonaco } from "@shikijs/monaco";
  import { getHighlighter } from "$lib/highlight";
  import { onDestroy, onMount } from "svelte";
  import { fade } from "svelte/transition";

  let container: HTMLDivElement;

  export let source: string;
  export let showLineNum = false;
  export let wrap = false;
  export let lang: string;

  let editor: monaco.editor.IStandaloneCodeEditor;

  onMount(async () => {
    const monaco = await import("monaco-editor-core");
    const highlighter = await getHighlighter(lang);
    monaco.languages.register({ id: lang });
    shikiToMonaco(highlighter, monaco);

    editor = monaco.editor.create(container, {
      value: source,
      language: lang,
      theme: "vitesse-dark",
      fontFamily: "fira code",
      smoothScrolling: true,
      lineHeight: 1.6,
      minimap: { enabled: false },
      fontLigatures: true,
      lineNumbers: showLineNum ? "interval" : "off",
      roundedSelection: false,
      cursorBlinking: "phase",
      wordWrap: wrap ? "on" : "off",
      cursorSmoothCaretAnimation: "explicit",
      renderLineHighlight: "all",
      renderLineHighlightOnlyWhenFocus: true,
      padding: { top: 24 },
      scrollBeyondLastLine: false,
      automaticLayout: true,
    });

    firstLoad = false;

    editor.onDidChangeModelContent(() => source = editor.getValue());
  });

  onDestroy(() => editor?.dispose());
</script>

<div bind:this={container} class="h-full w-full overflow-hidden transition-opacity duration-400" class:op-0={!editor && firstLoad} />

{#if !editor && firstLoad}
  <div class="absolute inset-0 grid place-items-center @container" out:fade>
    <div class="flex flex-row items-center gap-2 op-80">
      <div class="i-svg-spinners-90-ring-with-bg" />
      <div class="hidden text-sm tracking-wide @lg:block">initiating monaco editor</div>
    </div>
  </div>
{/if}
