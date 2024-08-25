<script context="module" lang="ts">
  import type { Item as AnyItem } from "./Item.svelte";

  import { writable } from "svelte/store";

  export const show = writable(false);
  export const commands = writable<Record<string, AnyItem[]>>({});
</script>

<script lang="ts">
  import Modal from "../Modal.svelte";
  import Item, { type Group } from "./Item.svelte";
  import { Command } from "cmdk-sv";

  const navigations = {
    type: "group",
    text: "Navigation",
    children: [
      { type: "link", href: "/", text: "Homepage" },
      { type: "link", href: "/console", text: "Immersive Console" },
      { type: "link", href: "/github", text: "Open a GitHub Repository" },
      { type: "link", href: "/cpython", text: "CPython Docs" },
    ],
  } as Group;

  $: items = [...Object.entries($commands).map(([text, children]) => ({ type: "group", text, children } as Group)), navigations];
</script>

<svelte:document on:keydown={(e) => {
  if (e.key === "k" && e.ctrlKey) {
    $show = !$show;
    e.preventDefault();
  }
}} />

<Modal bind:show={$show} closeOnClickOutside let:close>

  <Command.Root loop class="pointer-events-auto max-w-80vw w-md flex flex-col b-(1 neutral-7) rounded-lg bg-neutral-8/70 p-2em backdrop-blur-lg lg:w-lg <lg:text-sm">

    <Command.Input autofocus on:keydown={e => e.key === "Escape" && close()} class="w-full ws-nowrap bg-transparent py-2 outline-none placeholder-(text-white/30)" placeholder="Type a command or search..." />

    <Command.Separator class="mb-3 mt-2 b-1 b-white/10" />

    <Command.List>

      <Command.Empty>No results found.</Command.Empty>

      {#each items as item}
        <Item {item} callback={close} />
      {/each}

    </Command.List>

  </Command.Root>

</Modal>
