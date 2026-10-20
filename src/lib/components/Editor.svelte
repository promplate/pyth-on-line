<script module>
  let firstLoad = true;
</script>

<script lang="ts">
  import type monaco from "monaco-editor-core";

  import { commandMenu } from "./command/state.svelte";
  import { shikiToMonaco } from "@shikijs/monaco";
  import { getHighlighter } from "$lib/highlight";
  import { getAbortSignal, untrack } from "svelte";
  import { fade } from "svelte/transition";

  let { source = $bindable(), showLineNum = false, wrap = false, lang, onsave }: { source: string; showLineNum?: boolean; wrap?: boolean; lang: string; onsave?: (source: string) => void } = $props();

  // Keep an in-flight instance loading even when another editor finishes first.
  const showInitialLoading = firstLoad;
  let editor = $state.raw<monaco.editor.IStandaloneCodeEditor>();
  let core: typeof monaco;

  async function loadLanguage(language: string) {
    core.languages.register({ id: language });
    shikiToMonaco(await getHighlighter(language), core);
  }

  async function initializeEditor(container: HTMLDivElement, signal: AbortSignal) {
    [core] = await Promise.all([import("monaco-editor-core"), getHighlighter(lang)]);
    await loadLanguage(lang);

    if (signal.aborted)
      return;

    const instance = core.editor.create(container, {
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

    editor = instance;
    firstLoad = false;

    instance.onDidChangeModelContent(() => source = instance.getValue());

    // Actions scope keybindings to this editor; addCommand registers global shortcuts.
    const saveAction = instance.addAction({ id: "save", label: "Save", keybindings: [core.KeyMod.CtrlCmd | core.KeyCode.KeyS], run: () => onsave?.(source) });
    const menuAction = instance.addAction({ id: "shortcut-menu", label: "Open shortcut menu", keybindings: [core.KeyMod.CtrlCmd | core.KeyCode.KeyK], run: () => {
      commandMenu.show = true;
    } });
    instance.onDidDispose(() => {
      saveAction.dispose();
      menuAction.dispose();
    });
  }

  function reload(editor: monaco.editor.IStandaloneCodeEditor, source: string, language = lang) {
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

  function attachEditor(container: HTMLDivElement) {
    const signal = getAbortSignal();
    // Prop changes should update the existing model, not restart initialization.
    untrack(() => initializeEditor(container, signal));
    $effect(() => {
      if (editor)
        reload(editor, source, lang);
    });
    return () => editor?.dispose();
  }
</script>

<div {@attach attachEditor} class={["h-full w-full overflow-hidden transition-opacity duration-400", { "op-0": !editor && showInitialLoading }]} />

{#if !editor && showInitialLoading}
  <div class="absolute inset-0 grid place-items-center @container" out:fade>
    <div class="flex flex-row items-center gap-2 op-80">
      <div class="i-svg-spinners-90-ring-with-bg" />
      <div class="hidden text-sm tracking-wide @lg:block">initiating monaco editor</div>
    </div>
  </div>
{/if}
