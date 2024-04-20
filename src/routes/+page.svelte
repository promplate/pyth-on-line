<script lang="ts">
  import type { AutoComplete, Item, Status } from "$lib/components/console/HeadlessConsole.svelte";
  import type { PyProxy } from "pyodide/ffi";
  import type { ClipboardEventHandler, KeyboardEventHandler } from "svelte/elements";

  import { Err, In, Out, Repr } from "$lib/components/console";
  import HeadlessConsole from "$lib/components/console/HeadlessConsole.svelte";
  import ConsolePrompt from "$lib/components/ConsolePrompt.svelte";
  import Modal from "$lib/components/Modal.svelte";
  import { patchSource, reformatInputSource } from "$lib/pyodide/translate";
  import { pyodideReady } from "$lib/stores";
  import { afterUpdate, beforeUpdate, onMount } from "svelte";
  import { cubicIn, cubicOut } from "svelte/easing";
  import { scale } from "svelte/transition";

  let log: Item[] = [];

  const history: string[] = [];
  let index = -1;

  let input = "";
  let inputRef: HTMLInputElement;

  let pyConsole: PyProxy;
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

  let push: (source: string) => Promise<void>;

  onMount(async () => {
    history.unshift(...(JSON.parse(localStorage.getItem("console-history") || "[]") as string[]).slice(0, 200));
    inputRef.focus();
  });

  async function pushMany(lines: string[], wait = true, hidden = false) {
    for (const line of lines) {
      let promise: Promise<any>;
      if (hidden) {
        promise = pyConsole.push(line);
      }
      else {
        pushHistory(line);
        promise = push(line);
      }
      wait && (await promise);
    }
  }

  async function pushBlock(source: string, wait = true, hidden = false) {
    const lines = patchSource(source.replaceAll("\r\n", "\n")).split("\n");
    lines.length > 1 && (await pushMany(lines.slice(0, -1), wait, hidden));
    input = lines.at(-1)!;
  }

  let ready: boolean;

  function pushHistory(source: string) {
    if (source.trim() && source !== history[0]) {
      history.unshift(source);
      localStorage.setItem("console-history", JSON.stringify(history));
    }
  }

  function handleInput() {
    if (!pyConsole)
      return;
    push(input);
    pushHistory(input);
    input = "";
  }

  function setCusorToEnd() {
    requestAnimationFrame(() => inputRef.setSelectionRange(input.length, input.length));
  }

  const onPaste: ClipboardEventHandler<Document> = async (event) => {
    const text = event.clipboardData?.getData("text") ?? "";
    await pushBlock(input + text);
  };

  const onKeyDown: KeyboardEventHandler<Document> = (event) => {
    switch (event.key) {
      case "ArrowUp": {
        const text = history.at(++index);
        if (text) {
          input = text;
          setCusorToEnd();
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
        setCusorToEnd();
        break;
      }

      case "Tab": {
        event.preventDefault();
        if (!input.trim()) {
          input += " ".repeat(4);
        }
        else {
          const [results, position] = complete(input);
          if (results.length === 1) {
            input = input.slice(0, position) + results[0];
            setCusorToEnd();
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
          pyConsole.buffer.pop();
          if (lines.length === 1) {
            log = [...log.slice(0, -1)];
            input = lines[0] + input;
            status = "complete";
          }
          else {
            const lastLine = lines.pop()!;
            log = [...log.slice(0, -1), { type: "in", text: lines.join("\n") }];
            input = lastLine + input;
          }
          history.pop();
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
    if (!inputRef)
      return;

    const d = document.documentElement;

    const offsetBottom = d.scrollHeight - d.clientHeight - d.scrollTop;

    autoscroll = offsetBottom < 200;
  });

  afterUpdate(() => {
    const d = document.documentElement;
    autoscroll && d.scrollTo({ top: d.scrollHeight });
  });
</script>

<svelte:document on:keydown={onKeyDown} on:paste|preventDefault={onPaste} />

<svelte:body on:click|self={() => inputRef.focus()} />

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

<Modal show={focusedError !== undefined}>
  <svelte:fragment slot="content">
    {#await import("$lib/components/ErrorExplain.svelte") then { default: ErrorExplain }}
      <svelte:component this={ErrorExplain} bind:errorInfo={focusedError} />
    {/await}
  </svelte:fragment>
</Modal>
