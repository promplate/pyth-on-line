<script lang="ts">
  import type { AutoComplete, Item, Status } from "./console/HeadlessConsole.svelte";
  import type { ConsoleAPI } from "#py/console/console.js";
  import type { Snippet } from "svelte";
  import type { ClipboardEventHandler, KeyboardEventHandler } from "svelte/elements";

  import { Err, In, Out, Repr } from "./console";
  import HeadlessConsole from "./console/HeadlessConsole.svelte";
  import ConsolePrompt from "./ConsolePrompt.svelte";
  import Modal from "./Modal.svelte";
  import { pyodideState } from "#lib/pyodide/state.svelte.js";
  import { patchSource, reformatInputSource } from "#lib/utils/formatSource.js";
  import { onMount, untrack } from "svelte";

  const { container, class: klass = "p-3", children }: { container?: HTMLElement; class?: string; children?: Snippet<[{ ready: boolean }]> } = $props();

  let autofocus = $state(false);

  let log = $state.raw<Item[]>([]);

  const history: string[] = [];
  let index = -1;

  let input = $state("");
  let inputRef: HTMLInputElement;

  let pyConsole = $state.raw<ConsoleAPI>();
  let complete = $state.raw<AutoComplete>();
  let status = $state<Status>("complete");

  let focusedError = $state.raw<{ traceback: string; code: string }>();

  function showErrorExplain(index: number) {
    if (log[index]?.type !== "err")
      return;

    const traceback = log[index].text;

    const code = log
      .slice(0, index)
      .map(({ text, type }) => (type === "in" ? reformatInputSource(text) : text))
      .join("\n");

    focusedError = { traceback, code };
  }

  let disposed = false;
  let headless: ReturnType<typeof HeadlessConsole>;
  const push = (source: string) => headless.push(source);

  onMount(() => {
    history.unshift(...(JSON.parse(localStorage.getItem("console-history") || "[]") as string[]));
    if (window.self !== window.top) {
      autofocus = true;
      focusToInput();
    }
    return () => {
      disposed = true;
    };
  });

  $effect(() => {
    if (pyodideState.ready && pyConsole && location.hash) {
      const source = atob(decodeURIComponent(location.hash.slice(1)));
      // Only readiness should trigger startup code, not state read while executing it.
      untrack(() => pushBlock(source));
    }
  });

  async function pushMany(lines: string[], wait = true, hidden = false, finallySetInput = "") {
    const api = pyConsole;
    if (disposed || !api)
      return;
    let promise: Promise<any> | null = null;
    for (const line of lines) {
      if (disposed)
        return;
      if (hidden) {
        promise = api.push(line, true).future;
      }
      else {
        promise && (input = line);
        wait && (await promise);
        if (disposed)
          return;
        pushHistory(line);
        promise = push(line);
      }
    }
    if (disposed)
      return;
    input = finallySetInput;
    wait && (await promise);
  }

  async function pushBlock(source: string, wait = true, hidden = false) {
    const lines = patchSource(source.replaceAll("\r\n", "\n")).split("\n");
    await pushMany(lines.slice(0, -1), wait, hidden, lines.at(-1));
  }

  let ready = $state(false);

  function pushHistory(source: string) {
    if (source.trim() && source !== history[0]) {
      history.unshift(source);
      localStorage.setItem("console-history", JSON.stringify(history.slice(0, 200)));
    }
  }

  function handleInput() {
    if (!pyConsole)
      return;
    push(input);
    pushHistory(input);
    input = "";
  }

  function focusToInput(start?: number, end?: number) {
    if (disposed || !inputRef)
      return;
    inputRef.scrollIntoView({ block: "center" });
    inputRef.focus();
    if (start !== undefined) {
      requestAnimationFrame(() => inputRef?.setSelectionRange(start, end ?? start));
    }
  }

  const onPaste: ClipboardEventHandler<Document> = async (event) => {
    if (!pyConsole || !((event.target! as Node).contains(inputRef)))
      return;
    event.preventDefault();
    const text = event.clipboardData?.getData("text") ?? "";
    const textBefore = input.slice(0, inputRef.selectionStart!);
    const textAfter = input.slice(inputRef.selectionEnd!);
    const distanceToEnd = input.length - inputRef.selectionEnd!;
    await pushBlock(textBefore + text + textAfter);
    focusToInput(input.length - distanceToEnd);
  };

  const onKeyDown: KeyboardEventHandler<Document | HTMLInputElement> = (event) => {
    if (!((event.target! as Node).contains(inputRef)))
      return;
    if (!event.ctrlKey && !event.metaKey && !event.altKey && event.key.length === 1)
      focusToInput();
    else if (document.activeElement !== inputRef)
      return;

    switch (event.key) {
      case "ArrowUp": {
        const text = history.at(++index);
        if (text) {
          input = text;
          focusToInput(input.length);
        }
        else {
          index = history.length;
        }
        break;
      }

      case "ArrowDown": {
        index--;
        if (index <= -1) {
          input = "";
          index = -1;
          break;
        }
        input = history.at(index)!;
        focusToInput();
        break;
      }

      case "Tab": {
        event.preventDefault();
        const { selectionStart, selectionEnd } = inputRef;
        if (event.shiftKey || selectionStart !== selectionEnd || !input.slice(0, selectionStart!).trim()) {
          const startDistance = input.length - selectionStart!;
          const endDistance = input.length - selectionEnd!;
          if (event.shiftKey)
            input = input.replace(/ {0,4}/, "");
          else
            input = `    ${input}`;
          const start = Math.max(0, input.length - startDistance);
          const end = Math.max(0, input.length - endDistance);
          focusToInput(start, end);
        }
        else {
          if (!complete)
            break;
          const [results, position] = complete(input.slice(0, selectionStart!));
          if (results.length === 1) {
            const [result] = results;
            input = input.slice(0, position) + result + input.slice(selectionEnd!);
            focusToInput(position + result.length);
          }
        }
        index = -1;
        break;
      }

      case "Enter": {
        handleInput();
        index = -1;
        break;
      }

      case "Backspace": {
        if (inputRef.selectionStart === 0 && inputRef.selectionEnd === 0 && status === "incomplete" && pyConsole) {
          input = pyConsole.pop();
          history.at(0) === input && history.shift();
          index = -1;
          event.preventDefault();
        }
        break;
      }

      default: {
        index = -1;
      }
    }
  };

  const extras = $derived(` ${klass}`);
</script>

<svelte:document onkeydown={onKeyDown} onpaste={onPaste} />

<div class="w-full @container">
  <div class="w-full flex flex-col gap-0.7 overflow-x-scroll whitespace-pre-wrap break-all text-neutral-3 font-mono [&>div:hover]:(rounded-sm bg-white/2) [&>div]:(px-1.7 py-0.6 -mx-1.7 -my-0.6) {extras}">

    <HeadlessConsole bind:this={headless} {container} bind:ready bind:log bind:complete bind:pyConsole bind:status>
      {#snippet children({ loading })}
        {#each log as { type, text }, index}
          {#if type === "out"}
            <Out {text} />
          {:else if type === "in"}
            <In {text} onclick={() => push(text)} />
          {:else if type === "err"}
            <Err {text} onclick={() => showErrorExplain(index)} />
          {:else if type === "repr"}
            <Repr {text} />
          {/if}
        {/each}
        <div class={["group flex flex-row", { "animate-pulse": loading || !ready }]}>
          <ConsolePrompt prompt={status === "incomplete" ? "..." : ">>>"} />
          <!-- svelte-ignore a11y_autofocus -->
          <input {autofocus} bind:this={inputRef} class="w-full bg-transparent outline-none" bind:value={input} type="text" autocapitalize="off" spellcheck="false" autocomplete="off" autocorrect="off" />
        </div>
      {/snippet}
    </HeadlessConsole>

  </div>
</div>

<Modal show={!!focusedError} cleanup={() => focusedError = undefined}>
  {#snippet children(close)}
    {#if pyConsole}
      {#await import("./ErrorExplainer.svelte")}
        <div class="rounded bg-neutral-8 p-4">
          <p role="status">Loading error explainer...</p>
          <button class="mt-2 underline" onclick={close}>Cancel</button>
        </div>
      {:then { default: ErrorExplainer }}
        <ErrorExplainer errorInfo={focusedError} {close} {pushBlock} {pyConsole} />
      {:catch}
        <div class="rounded bg-neutral-8 p-4">
          <p role="alert">Unable to load the error explainer. Reload the page to try again.</p>
          <button class="mt-2 underline" onclick={close}>Close</button>
        </div>
      {/await}
    {/if}
  {/snippet}
</Modal>

{@render children?.({ ready })}
