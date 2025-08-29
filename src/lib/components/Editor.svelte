<script module>
  let firstLoad = true;
</script>

<script lang="ts">
  import type monaco from "monaco-editor-core";

  import { show as showMenu } from "./command/CmdK.svelte";
  import { shikiToMonaco } from "@shikijs/monaco";
  import { getHighlighter } from "$lib/highlight";
  import { createEventDispatcher, onDestroy, onMount } from "svelte";
  import { run } from "svelte/legacy";
  import { fade } from "svelte/transition";

  let container: HTMLDivElement = $state();

  interface Props {
    source: string;
    showLineNum?: boolean;
    wrap?: boolean;
    lang: string;
  }

  let {
    source = $bindable(),
    showLineNum = false,
    wrap = false,
    lang,
  }: Props = $props();

  let editor: monaco.editor.IStandaloneCodeEditor = $state();
  let core: typeof monaco;

  async function loadLanguage(language: string) {
    core.languages.register({ id: language });
    shikiToMonaco(await getHighlighter(language), core);
  }

  const dispatch = createEventDispatcher<{
    save: string;
  }>();

  onMount(async () => {
    [core] = await Promise.all([import("monaco-editor-core"), getHighlighter(lang)]);
    await loadLanguage(lang);

    if (!container)
      return;

    editor = core.editor.create(container, {
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

    editor.addCommand(core.KeyMod.CtrlCmd | core.KeyCode.KeyS, () => dispatch("save", source));
    editor.addCommand(core.KeyMod.CtrlCmd | core.KeyCode.KeyK, () => $showMenu = true);
  });

  onDestroy(() => editor?.dispose());

  function reload(source: string, language = lang) {
    if (language !== editor.getModel()!.getLanguageId()) {
      core.editor.setModelLanguage(editor.getModel()!, language);
      loadLanguage(language);
    }
    if (source !== editor.getValue()) {
      editor.setValue(source);
      editor.updateOptions({ detectIndentation: false });
      editor.updateOptions({ detectIndentation: true });
    }
  }

  run(() => {
    editor && reload(source, lang);
  });
</script>

<div bind:this={container} class="h-full w-full overflow-hidden transition-opacity duration-400" class:op-0={!editor && firstLoad}></div>

{#if !editor && firstLoad}
  <div class="absolute inset-0 grid place-items-center @container" out:fade>
    <div class="flex flex-row items-center gap-2 op-80">
      <div class="i-svg-spinners-90-ring-with-bg"></div>
      <div class="hidden text-sm tracking-wide @lg:block">initiating monaco editor</div>
    </div>
  </div>
{/if}
