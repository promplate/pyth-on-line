<script lang="ts">
  import type { Folder, Tree } from "$lib/utils/list2tree";

  import { slide } from "svelte/transition";

  export let folder: Folder;
  export let parent = "";
  export let focusedFile: string | null = null;

  $: tree = folder.children;
  $: collapse = folder.collapse ?? tree.length > 20;

  export let depth = 0;

  function getPath(item: Tree[number]) {
    return parent ? `${parent}/${item.name}` : item.name;
  }

  function countFlattenLength(children = tree) {
    let length = 0;
    for (const item of children) {
      if (item.type === "folder" && !item.collapse)
        length += countFlattenLength(item.children);
      else
        length += 1;
    }
    return length;
  }
</script>

<div>
  {#if parent !== ""}
    <button style:--depth="{depth - 1 + 0.7}em" on:click={() => (folder.collapse = !collapse)}>
      {parent.split("/").at(-1)}
    </button>
  {/if}

  {#if parent === "" || !collapse}

    <div transition:slide={{ duration: 100 * (countFlattenLength() ** 0.5) }}>

      {#each tree as item}
        {#if item.type === "file"}
          <button style:--depth="{depth + 0.7}em" class:!bg-neutral-8={focusedFile === getPath(item)} on:click={() => (focusedFile = getPath(item))}>
            {item.name}
          </button>
        {:else}
          <svelte:self folder={item} parent={getPath(item)} depth={depth + 1} bind:focusedFile />
        {/if}
      {/each}

    </div>

  {/if}
</div>

<style>
  div {
    --uno: flex flex-col text-ellipsis ws-nowrap;
  }

  button {
    --uno: w-full shrink-0 overflow-x-hidden rounded-r-sm py-0.6 pl-$depth pr-1 text-left text-xs text-neutral-1/95 font-mono transition-background-color duration-100 active:bg-neutral-8/70 hover:bg-neutral-8/50;
  }
</style>
