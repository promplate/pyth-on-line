<script context="module" lang="ts">
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
  import { browser } from "$app/environment";
  import { beforeNavigate, preloadData } from "$app/navigation";
  import { Command } from "cmdk-sv";

  export let item: Item;

  // eslint-disable-next-line no-undef-init
  export let callback: (() => any) | undefined = undefined;

  let acted = false;

  beforeNavigate(({ complete }) => {
    acted && complete.then(callback);
  });
</script>

{#if item.type === "group"}

  <Command.Group asChild let:container let:heading let:group>
    <div {...container.attrs} use:container.action class:hidden={container.attrs.hidden}>
      <h6 {...heading.attrs} class="my-1 w-full flex flex-col text-xs tracking-widest op-40">
        {item.text}
      </h6>
      <div {...group.attrs} class="flex flex-col">
        {#each item.children as child}
          <svelte:self item={child} {callback} />
        {/each}
      </div>
    </div>

  </Command.Group>

{:else if item.type === "link"}

  <Command.Item value={item.text} onSelect={() => acted = true} asChild let:action let:attrs>
    {@const highlighted = attrs["data-selected"]}
    <a href={item.href} use:action {...attrs} class:highlighted>
      <!-- eslint-disable-next-line no-sequences -->
      {(browser && highlighted && preloadData(item.href)), item.text}
    </a>
  </Command.Item>

{:else if item.type === "cmd"}

  <Command.Item value={item.text} onSelect={value => (async () => item.callback(value))().finally(callback)} alwaysRender={item.alwaysRender} asChild let:action let:attrs>
    <button class="text-left" use:action {...attrs} class:highlighted={attrs["data-selected"]}>
      {item.text}
    </button>
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
