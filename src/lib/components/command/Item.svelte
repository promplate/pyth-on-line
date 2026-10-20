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
  import Self from "./Item.svelte";
  import { browser } from "$app/env";
  import { beforeNavigate, preloadData } from "$app/navigation";
  import { Command } from "cmdk-sv";
  import { fromAction } from "svelte/attachments";

  const { item, callback }: { item: Item; callback?: () => any } = $props();

  let acted = false;

  beforeNavigate(({ complete }) => {
    acted && complete.then(callback);
  });
</script>

{#if item.type === "group"}

  <!-- cmdk-sv 0.0.19 still exposes builders through legacy slots. -->
  <Command.Group asChild let:container let:heading let:group>
    <div {...container.attrs} {@attach fromAction((node: HTMLElement) => container.action(node))} class={{ hidden: container.attrs.hidden }}>
      <h6 {...heading.attrs} class="my-1 w-full flex flex-col text-xs tracking-widest op-40">
        {item.text}
      </h6>
      <div {...group.attrs} class="flex flex-col">
        <!-- Registered items keep their identity; labels may repeat. -->
        {#each item.children as child (child)}
          <Self item={child} {callback} />
        {/each}
      </div>
    </div>

  </Command.Group>

{:else if item.type === "link"}

  <Command.Item value={item.text} onSelect={() => acted = true} asChild let:action let:attrs>
    {@const highlighted = attrs["data-selected"]}
    <a href={item.href} {@attach fromAction((node: HTMLElement) => action(node))} {...attrs} class={{ highlighted }}>
      <!-- eslint-disable-next-line no-sequences -->
      {(browser && highlighted && preloadData(item.href)), item.text}
    </a>
  </Command.Item>

{:else if item.type === "cmd"}

  <Command.Item value={item.text} onSelect={value => (async () => item.callback(value))().finally(callback)} alwaysRender={item.alwaysRender} asChild let:action let:attrs>
    <button class={["text-left", { highlighted: attrs["data-selected"] }]} {@attach fromAction((node: HTMLElement) => action(node))} {...attrs}>
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
