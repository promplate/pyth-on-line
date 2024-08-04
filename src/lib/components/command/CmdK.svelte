<script lang="ts">
  import Modal from "../Modal.svelte";
  import Item, { type Group } from "./Item.svelte";
  import { Command } from "cmdk-sv";

  export let show = false;

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

  $: items = [navigations];
</script>

<svelte:document on:keydown={(e) => {
  if (e.key === "k" && e.ctrlKey) {
    show = !show;
    e.preventDefault();
  }
}} />

<Modal bind:show closeOnClickOutside>

  <Command.Root loop slot="content" class="pointer-events-auto max-w-80vw w-md flex flex-col b-(1 neutral-7) rounded-lg bg-neutral-8/70 p-2em backdrop-blur-lg lg:w-lg <lg:text-sm">

    <Command.Input autofocus on:keydown={e => e.key === "Escape" && (show = false)} class="w-full ws-nowrap bg-transparent py-2 outline-none placeholder-(text-white/30)" placeholder="Type a command or search..." />

    <Command.Separator class="mb-3 mt-2 b-1 b-white/10" />

    <Command.List>

      <Command.Empty>No results found.</Command.Empty>

      {#each items as item}
        <Item {item} callback={() => show = false} />
      {/each}

    </Command.List>

  </Command.Root>

</Modal>
