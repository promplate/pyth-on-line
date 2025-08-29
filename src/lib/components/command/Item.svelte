<script module lang="ts">
  interface BaseItem {
    text: string;
    alwaysRender?: boolean;
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
  import Item from "./Item.svelte";
  import { browser } from "$app/environment";
  import { beforeNavigate, preloadData } from "$app/navigation";
  import { Command } from "cmdk-sv";

  interface Props {
    item: Item;

    callback?: (() => any) | undefined;
  }

  const { item, callback = undefined }: Props = $props();

  let acted = $state(false);

  beforeNavigate(({ complete }) => {
    acted && complete.then(callback);
  });
</script>

{#if item.type === "group"}

  <Command.Group asChild>
    {#snippet children({ container, heading, group })}
      <div {...container.attrs} use:container.action class:hidden={container.attrs.hidden}>
        <h6 {...heading.attrs} class="my-1 w-full flex flex-col text-xs tracking-widest op-40">
          {item.text}
        </h6>
        <div {...group.attrs} class="flex flex-col">
          {#each item.children as child}
            <Item item={child} {callback} />
          {/each}
        </div>
      </div>

    {/snippet}
  </Command.Group>

{:else if item.type === "link"}

  <Command.Item value={item.text} onSelect={() => acted = true} asChild>
    {#snippet children({ action, attrs })}
      {@const highlighted = attrs["data-selected"]}
      <a href={item.href} use:action {...attrs} class:highlighted>
        <!-- eslint-disable-next-line no-sequences -->
        {(browser && highlighted && preloadData(item.href)), item.text}
      </a>
    {/snippet}
  </Command.Item>

{:else if item.type === "cmd"}

  <Command.Item value={item.text} onSelect={value => (async () => item.callback(value))().finally(callback)} alwaysRender={item.alwaysRender} asChild>
    {#snippet children({ action, attrs })}
      <button class="text-left" use:action {...attrs} class:highlighted={attrs["data-selected"]}>
        {item.text}
      </button>
    {/snippet}
  </Command.Item>

{/if}

<style>
  a, button {
    --uno: w-[calc(100%+1rem)] rounded-md p-2 -mx-2;
  }

  .highlighted {
    --uno: bg-white/5;
  }
</style>
