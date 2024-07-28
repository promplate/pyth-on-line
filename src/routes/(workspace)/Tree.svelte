<script context="module" lang="ts">
  const collapsedItems = new Set<string>();
</script>

<script lang="ts">
  import type { File, Folder, Tree } from "$lib/utils/list2tree";

  import { slide } from "svelte/transition";

  export let folder: Folder;
  export let parent = "";
  export let focusedFile: string | null = null;

  let collapse: boolean;

  $: tree = folder.children;
  $: {
    const fullPath = getPath(folder);
    if (collapse === undefined)
      collapse = collapsedItems.has(fullPath) || folder.children.length > 20;
    else
      collapse ? collapsedItems.add(fullPath) : collapsedItems.delete(fullPath);
  }

  export let depth = 0;

  function getPath(item: Tree[number]) {
    return parent ? `${parent}/${item.name}` : item.name;
  }

  function countFlattenLength(children: Tree) {
    let length = 0;
    for (const item of children) {
      length++;
      if (item.type === "folder" && !collapsedItems.has(getPath(item)))
        length += countFlattenLength(item.children);
    }
    return length;
  }

  function getFileIcon(item: File) {
    switch (item.name.split(".").at(-1)) {
      case "py":
        return "i-catppuccin-python";
      case "j2":
        return "i-catppuccin-jinja";
      default:
        return "i-catppuccin-file";
    }
  }
</script>

<section>
  {#if parent !== ""}
    <button style:--depth="{depth - 1 + 0.8}em" on:click={() => collapse = !collapse}>
      <div class={collapse ? "i-catppuccin-folder" : "i-catppuccin-folder-open"} />
      <div>{parent.split("/").at(-1)}</div>
    </button>
  {/if}

  {#if parent === "" || !collapse}

    <section transition:slide={{ duration: 100 * (countFlattenLength(tree) ** 0.5) }}>

      {#each tree as item}
        {#if item.type === "file"}
          <button style:--depth="{depth + 0.8}em" class:!bg-neutral-8={focusedFile === getPath(item)} on:click={() => (focusedFile = getPath(item))}>
            <div class={getFileIcon(item)} />
            <div>{item.name}</div>
          </button>
        {:else}
          <svelte:self folder={item} parent={getPath(item)} depth={depth + 1} bind:focusedFile />
        {/if}
      {/each}

    </section>

  {/if}
</section>

<style>
  section {
    --uno: flex flex-col text-ellipsis ws-nowrap;
  }

  button {
    --uno: w-full flex shrink-0 flex-row items-center gap-1.4 overflow-x-hidden rounded-r-sm py-0.6 pl-$depth pr-1 text-left text-xs text-neutral-1/95 font-mono transition-background-color duration-100 active:bg-neutral-8/70 hover:bg-neutral-8/50;
  }

  div {
    --uno: shrink-0;
  }
</style>
