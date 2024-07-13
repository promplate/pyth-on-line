<script lang="ts">
  import type { AutoComplete, Item, Status } from "$lib/components/console/HeadlessConsole.svelte";
  import type { ConsoleAPI } from "$py/console/console";
  import type { ClipboardEventHandler, KeyboardEventHandler } from "svelte/elements";

  import { Err, In, Out, Repr } from "$lib/components/console";
  import HeadlessConsole from "$lib/components/console/HeadlessConsole.svelte";
  import ConsolePrompt from "$lib/components/ConsolePrompt.svelte";
  import Modal from "$lib/components/Modal.svelte";
  import { currentPushBlock, pyodideReady } from "$lib/stores";
  import { patchSource, reformatInputSource } from "$lib/utils/formatSource";
  import { needScroll, scrollToBottom } from "$lib/utils/scroll";
  import { afterUpdate, beforeUpdate, onMount } from "svelte";
  import { cubicIn, cubicOut } from "svelte/easing";
  import { scale } from "svelte/transition";

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

    $currentPushBlock = source => pushBlock(source, false);

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
          const item = log.at(-1)!;
          const lines = item.text.split("\n");
          pyConsole.pop();
          if (lines.length === 1) {
            log = [...log.slice(0, -1)];
            input = lines[0] + input;
            status = "complete";
          }
          else {
            const lastLine = lines.pop()!;
            log = [...log.slice(0, -1), { type: "in", text: lines.join("\n"), incomplete: true }];
            input = lastLine + input;
          }
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

  let autoscroll = false;

  beforeUpdate(() => {
    autoscroll = needScroll(document.documentElement, 500);
  });

  afterUpdate(() => {
    autoscroll && scrollToBottom(document.documentElement);
  });
</script>

<svelte:document on:keydown={onKeyDown} on:paste|preventDefault={onPaste} />

<div class="my-4 w-[calc(100vw-2rem)] flex flex-row gap-4 break-all p-3 text-neutral-3 <lg:(my-3 w-[calc(100vw-1.5rem)] gap-3 p-2 text-sm) <sm:(my-2 w-[calc(100vw-1rem)] gap-2 p-1 text-xs) [&>div]:(overflow-x-scroll rounded bg-white/3 p-5 <lg:p-4 <sm:p-3)">
  <div class="w-full flex flex-col gap-0.7 whitespace-pre-wrap font-mono [&>div:hover]:(rounded-sm bg-white/2 px-1.7 py-0.6 -mx-1.7 -my-0.6)">
    <HeadlessConsole bind:ready bind:log bind:push bind:complete bind:pyConsole bind:status let:loading>
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
</div>

<Modal show={!$pyodideReady || !ready}>
  <svelte:fragment slot="content">
    {#await Promise.resolve() then _}
      <div in:scale={{ easing: cubicOut, start: 0.8 }} out:scale|global={{ easing: cubicIn, start: 0.9 }} class="rounded-lg bg-white/3 p-4 text-white/70">
        <div class="i-svg-spinners-90-ring-with-bg text-xl" />
      </div>
    {/await}
  </svelte:fragment>
</Modal>

{#await import("$lib/components/ErrorExplainer.svelte") then { default: ErrorExplainer }}
  <Modal show={focusedError !== undefined}>
    <svelte:fragment slot="content">
      <svelte:component this={ErrorExplainer} bind:errorInfo={focusedError} />
    </svelte:fragment>
  </Modal>
{/await}
