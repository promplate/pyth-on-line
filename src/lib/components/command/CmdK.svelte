<script lang="ts">
  import type { Group } from "./Item.svelte";

  import Modal from "../Modal.svelte";
  import Item from "./Item.svelte";
  import { commandMenu } from "./state.svelte";
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

  const rootItems = $derived([...Object.entries(commandMenu.commands).map(([text, children]) => ({ type: "group", text, children } as Group)), navigations]);
  const items = $derived(commandMenu.getItems?.(commandMenu.input));
</script>

<svelte:document onkeydown={(e) => {
  if (e.key === "k" && (e.ctrlKey || e.metaKey)) {
    if (!e.repeat)
      commandMenu.show = !commandMenu.show;
    e.preventDefault();
  }
}} />

<Modal bind:show={commandMenu.show} closeOnClickOutside cleanup={() => commandMenu.input = ""}>
  {#snippet children(close)}

    <Command.Root loop onKeydown={e => e.key === "Escape" && close()} class="pointer-events-auto max-w-80vw w-md flex flex-col b-(1 neutral-7) rounded-lg bg-neutral-8/70 p-2em pb-0 backdrop-blur-lg lg:w-lg <lg:text-sm">

      {#if commandMenu.prefixes.length}
        <div class="mb-1 flex flex-row items-center gap-1.5 text-xs text-white/80 font-mono">
          <div class="select-none font-bold">&gt;</div>
          {#each commandMenu.prefixes as prefix}
            <div class="rounded bg-white/5 px-1.5 py-0.5">{prefix}</div>
          {/each}
        </div>
      {/if}

      <Command.Input autofocus bind:value={commandMenu.input} class="w-full ws-nowrap bg-transparent py-2 outline-none placeholder-(text-white/30)" placeholder={commandMenu.placeholder || "Type a command or search..."} />

      <Command.Separator alwaysRender class="mt-1.5 b-1 b-white/10" />

      <Command.List class="max-h-60vh overflow-y-scroll px-2 pb-2em pt-3 -mx-2">

        {#if !commandMenu.prefixes.length}
          <Command.Empty>No results found.</Command.Empty>
        {/if}

        {#if items}
          {#each items as item}
            <Item {item} callback={close} />
          {/each}
        {:else}
          <!-- Group wrappers are derived anew; each registration keeps its children array. -->
          {#each rootItems as item (item.children)}
            <Item {item} callback={close} />
          {/each}
        {/if}

      </Command.List>

    </Command.Root>

  {/snippet}
</Modal>
