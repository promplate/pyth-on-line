<script context="module" lang="ts">
  interface BaseItem {
    text: string;
  }

  export interface Link extends BaseItem {
    type: "link";
    href: string;
  }

  export interface Cmd extends BaseItem {
    type: "cmd";
    callback(text: string): any;
  }

  export interface Group extends BaseItem {
    type: "group";
    children: (Link | Cmd | Group)[];
  }

  export type Item = Link | Cmd | Group;
</script>

<script lang="ts">
  import { browser } from "$app/environment";
  import { preloadData } from "$app/navigation";
  import { Command } from "cmdk-sv";

  export let item: Item;
</script>

{#if item.type === "group"}

  <Command.Group asChild let:container let:heading let:group>
    <div {...container.attrs} use:container.action class:hidden={container.attrs.hidden}>
      <h6 {...heading.attrs} class="my-1 w-full flex flex-col text-xs tracking-widest op-40">
        {item.text}
      </h6>
      <div {...group.attrs} class="flex flex-col">
        {#each item.children as child}
          <svelte:self item={child} />
        {/each}
      </div>
    </div>

  </Command.Group>

{:else if item.type === "link"}

  <Command.Item asChild let:action let:attrs>
    <!-- eslint-disable-next-line no-unused-vars -->
    {@const _ = (browser && attrs["data-selected"] && preloadData(item.href))}
    <a href={item.href} use:action {...attrs} class:selected={attrs["data-selected"]}>
      {item.text}
    </a>
  </Command.Item>

{:else if item.type === "cmd"}

  <Command.Item onSelect={item.callback} asChild let:action let:attrs>
    <button use:action {...attrs} class:selected={attrs["data-selected"]}>
      {item.text}
    </button>
  </Command.Item>

{/if}

<style>
    a, button {
        --uno: block w-full rounded-md p-2 -mx-2;
    }

    .selected {
        --uno: bg-white/5;
    }
</style>
