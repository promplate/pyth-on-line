<script context="module" lang="ts">
  import type { Item as AnyItem } from "./Item.svelte";

  import { writable } from "svelte/store";

  export const show = writable(false);
  export const commands = writable<Record<string, AnyItem[]>>({});
  export const items = writable<AnyItem[]>([]);
  export const prefixes = writable<string[]>([]);
  export const input = writable("");
  export const placeholder = writable("");
</script>

<script lang="ts">
  import type { Group } from "./Item.svelte";

  import Modal from "../Modal.svelte";
  import Item from "./Item.svelte";
  import { Command } from "cmdk-sv";

  const navigations = {
    type: "group",
    text: "导航",
    children: [
      { type: "link", href: "/", text: "首页" },
      { type: "link", href: "/console", text: "Python 控制台" },
      { type: "link", href: "/github", text: "打开 GitHub 仓库" },
      { type: "link", href: "/cpython", text: "CPython 官方文档" },
    ],
  } as Group;

  $: rootItems = [...Object.entries($commands).map(([text, children]) => ({ type: "group", text, children } as Group)), navigations];
</script>

<svelte:document on:keydown={(e) => {
  if (e.key === "k" && e.ctrlKey) {
    $show = !$show;
    e.preventDefault();
  }
}} />

<Modal bind:show={$show} closeOnClickOutside let:close cleanup={() => $input = ""}>

  <Command.Root loop onKeydown={e => e.key === "Escape" && close()} class="pointer-events-auto max-w-80vw w-md flex flex-col b-(1 neutral-7) rounded-lg bg-neutral-8/70 p-2em pb-0 backdrop-blur-lg lg:w-lg <lg:text-sm">

    {#if $prefixes.length}
      <div class="mb-1 flex flex-row items-center gap-1.5 text-xs text-white/80 font-mono">
        <div class="select-none font-bold">&gt;</div>
        {#each $prefixes as prefix}
          <div class="rounded bg-white/5 px-1.5 py-0.5">{prefix}</div>
        {/each}
      </div>
    {/if}

    <Command.Input autofocus bind:value={$input} class="w-full ws-nowrap bg-transparent py-2 outline-none placeholder-(text-white/30)" placeholder={$placeholder || "输入或搜索……"} />

    <Command.Separator alwaysRender class="mt-1.5 b-1 b-white/10" />

    <Command.List class="max-h-60vh overflow-y-scroll px-2 pb-2em pt-3 -mx-2">

      {#if !$prefixes.length}
        <Command.Empty>No results found.</Command.Empty>
      {/if}

      {#each $items.length ? $items : rootItems as item}
        <Item {item} callback={close} />
      {/each}

    </Command.List>

  </Command.Root>

</Modal>
