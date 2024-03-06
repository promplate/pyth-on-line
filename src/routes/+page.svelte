<script lang="ts">
  import type { AutoComplete, Item } from "$lib/components/console/HeadlessConsole.svelte";
  import type { PyProxy } from "pyodide/ffi";
  import type { KeyboardEventHandler } from "svelte/elements";

  import { Err, In, Out, Repr } from "$lib/components/console";
  import HeadlessConsole from "$lib/components/console/HeadlessConsole.svelte";
  import ConsolePrompt from "$lib/components/ConsolePrompt.svelte";
  import Modal from "$lib/components/Modal.svelte";
  import { reformatInputSource } from "$lib/pyodide/translate";
  import { pyodideReady } from "$lib/stores";
  import { onMount } from "svelte";
  import { cubicIn, cubicOut } from "svelte/easing";
  import { scale } from "svelte/transition";

  let log: Item[] = [];

  const history: string[] = [];
  let index = -1;

  let input = "";
  let inputRef: HTMLInputElement;

  let pyConsole: PyProxy;
  let complete: AutoComplete;

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

  let pushLog: (item: Item, behind?: Item) => Item | undefined;

  let push: (source: string) => Promise<void>;

  onMount(async () => {
    history.unshift(...(JSON.parse(localStorage.getItem("console-history") || "[]") as string[]).slice(0, 200));
    inputRef.focus();
  });

  async function pushMany(lines: string[], wait: boolean, hidden?: boolean) {
    for (const line of lines) {
      const promise = hidden ? pyConsole.push(line) : push(line);
      wait && (await promise);
    }
  }

  let ready: boolean;

  function handleInput() {
    push(input);
    if (input.trim() && input !== history[0]) {
      history.unshift(input);
      localStorage.setItem("console-history", JSON.stringify(history));
    }
    input = "";
  }

  function setCusorToEnd() {
    requestAnimationFrame(() => inputRef.setSelectionRange(input.length, input.length));
  }

  const onKeyDown: KeyboardEventHandler<HTMLInputElement> = (event) => {
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

      default: {
        index = -1;
      }
    }
  };
</script>

<div class="my-4 w-[calc(100vw-2rem)] flex flex-row gap-4 p-3 text-neutral-3 <lg:(my-3 w-[calc(100vw-1.5rem)] gap-3 p-2 text-sm) <sm:(my-2 w-[calc(100vw-1rem)] gap-2 p-1 text-xs) [&>div]:(overflow-x-scroll rounded bg-white/3 p-5 <lg:p-4 <sm:p-3)">
  <div class="w-full flex flex-col gap-0.7 whitespace-pre-wrap font-mono [&>div:hover]:(rounded-sm bg-white/2 px-1.7 py-0.6 -mx-1.7 -my-0.6)">
    <HeadlessConsole bind:ready bind:log bind:push bind:pushLog bind:complete bind:pyConsole let:status let:loading>
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
        <input autofocus bind:this={inputRef} class="w-full bg-transparent outline-none" bind:value={input} type="text" on:keydown={onKeyDown} />
      </div>
    </HeadlessConsole>
  </div>
</div>

<Modal show={!$pyodideReady}>
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
