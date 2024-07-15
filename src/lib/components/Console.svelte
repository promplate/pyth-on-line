<script lang="ts">
  import type { AutoComplete, Item, Status } from "./console/HeadlessConsole.svelte";
  import type { ConsoleAPI } from "$py/console/console";
  import type { ClipboardEventHandler, KeyboardEventHandler } from "svelte/elements";

  import { Err, In, Out, Repr } from "./console";
  import HeadlessConsole from "./console/HeadlessConsole.svelte";
  import ConsolePrompt from "./ConsolePrompt.svelte";
  import Modal from "./Modal.svelte";
  import { pyodideReady } from "$lib/stores";
  import { patchSource, reformatInputSource } from "$lib/utils/formatSource";
  import { onMount } from "svelte";

  export let container: HTMLElement | undefined;

  let log: Item[] = [];

  const history: string[] = [];
  let index = -1;

  let input = "";
  let inputRef: HTMLInputElement;

  let pyConsole: ConsoleAPI;
  let complete: AutoComplete;
  let status: Status;

  let focusedError: { traceback: string; code: string };

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

  let push: (source: string) => Promise<any>;

  onMount(async () => {
    history.unshift(...(JSON.parse(localStorage.getItem("console-history") || "[]") as string[]));
    focusToInput();
  });

  $: if ($pyodideReady && pyConsole) {
    if (location.hash) {
      const source = atob(decodeURIComponent(location.hash.slice(1)));
      location.hash = "";
      pushBlock(source);
    }
  }

  async function pushMany(lines: string[], wait = true, hidden = false, finallySetInput = "") {
    let promise: Promise<any> | null = null;
    for (const line of lines) {
      if (hidden) {
        promise = pyConsole.push(line).future;
      }
      else {
        promise && (input = line);
        wait && (await promise);
        pushHistory(line);
        promise = push(line);
      }
    }
    input = finallySetInput;
    wait && (await promise);
  }

  async function pushBlock(source: string, wait = true, hidden = false) {
    const lines = patchSource(source.replaceAll("\r\n", "\n")).split("\n");
    await pushMany(lines.slice(0, -1), wait, hidden, lines.at(-1));
  }

  let ready: boolean;

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
    inputRef.scrollIntoView({ block: "center" });
    inputRef.focus();
    if (start !== undefined) {
      requestAnimationFrame(() => inputRef.setSelectionRange(start, end ?? start));
    }
  }

  const onPaste: ClipboardEventHandler<Document> = async (event) => {
    const text = event.clipboardData?.getData("text") ?? "";
    const textBefore = input.slice(0, inputRef.selectionStart!);
    const textAfter = input.slice(inputRef.selectionEnd!);
    const distanceToEnd = input.length - inputRef.selectionEnd!;
    await pushBlock(textBefore + text + textAfter);
    focusToInput(input.length - distanceToEnd);
  };

  const onKeyDown: KeyboardEventHandler<Document> = (event) => {
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
        if (inputRef.selectionStart === 0 && inputRef.selectionEnd === 0 && status === "incomplete") {
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
</script>

<svelte:document on:keydown={onKeyDown} on:paste|preventDefault={onPaste} />

<div class="w-full flex flex-col gap-0.7 overflow-x-scroll whitespace-pre-wrap rounded bg-white/3 p-5 font-mono [&>div:hover]:(rounded-sm bg-white/2 px-1.7 py-0.6 -mx-1.7 -my-0.6) <lg:p-4 <sm:p-3">

  <HeadlessConsole {container} bind:ready bind:log bind:push bind:complete bind:pyConsole bind:status let:loading>
    {#each log as { type, text }, index}
      {#if type === "out"}
        <Out {text} />
      {:else if type === "in"}
        <In {text} on:click={() => push(text)} />
      {:else if type === "err"}
        <Err {text} on:click={() => showErrorExplain(index)} />
      {:else if type === "repr"}
        <Repr {text} />
      {/if}
    {/each}
    <div class="group flex flex-row" class:animate-pulse={loading || !ready}>
      <ConsolePrompt prompt={status === "incomplete" ? "..." : ">>>"} />
      <!-- svelte-ignore a11y-autofocus -->
      <input autofocus bind:this={inputRef} class="w-full bg-transparent outline-none" bind:value={input} type="text" />
    </div>
  </HeadlessConsole>

</div>

{#await import("./ErrorExplainer.svelte") then { default: ErrorExplainer }}
  <Modal show={focusedError !== undefined}>
    <svelte:fragment slot="content">
      <svelte:component this={ErrorExplainer} bind:errorInfo={focusedError} {pushBlock} />
    </svelte:fragment>
  </Modal>
{/await}

<slot {ready} />