<script module lang="ts">
  const collapseStates = new Map<string, boolean>();
</script>

<script lang="ts">
  import type { File, Folder, Tree } from "$lib/utils/list2tree";

  import Tree_1 from "./Tree.svelte";
  import { run } from "svelte/legacy";
  import { slide } from "svelte/transition";

  let collapse = $state(collapseStates.get(parent) ?? folder.children.length > 20);

  interface Props {
    folder: Folder;
    parent?: string;
    focusedFile?: string | null;
    depth?: number;
  }

  let {
    folder,
    parent = "",
    focusedFile = $bindable(null),
    depth = 0,
  }: Props = $props();

  function getPath(item: Tree[number]) {
    return parent ? `${parent}/${item.name}` : item.name;
  }

  function countFlattenLength(children: Tree) {
    let length = 0;
    for (const item of children) {
      length++;
      if (item.type === "folder" && !(collapseStates.get(getPath(item)) ?? item.children.length > 5))
        length += countFlattenLength(item.children);
    }
    return length;
  }

  function getFileIcon(item: File) {
    switch (item.name.split(".").at(-1)) {
      case "py":
      case "pyi":
        return "i-catppuccin-python";
      case "j2":
        return "i-catppuccin-jinja";
      case "svelte":
        return "i-catppuccin-svelte";
      case "yml":
      case "yaml":
        return "i-catppuccin-yaml";
      case "toml":
        return "i-catppuccin-toml";
      case "ts":
      case "mts":
      case "cts":
        return "i-catppuccin-typescript";
      case "js":
      case "mjs":
      case "cjs":
        return "i-catppuccin-javascript";
      case "md":
        return "i-catppuccin-markdown";
      default:
        return "i-catppuccin-file";
    }
  }
  run(() => {
    collapseStates.set(parent, collapse);
  });
  const tree = $derived(folder.children);
</script>

<section data-container>
  {#if parent !== ""}
    <button style:--depth="{depth - 1 + 0.8}em" onclick={() => collapse = !collapse}>
      <div class={collapse ? "i-catppuccin-folder" : "i-catppuccin-folder-open"}></div>
      <div>{parent.split("/").at(-1)}</div>
    </button>
  {/if}

  {#if parent === "" || !collapse}

    <section transition:slide={{ duration: 100 * (countFlattenLength(tree) ** 0.4) }}>

      {#each tree as item}
        {#if item.type === "file"}
          <button style:--depth="{depth + 0.8}em" class:!bg-neutral-8={focusedFile === getPath(item)} onclick={() => (focusedFile = getPath(item))}>
            <div class={getFileIcon(item)}></div>
            <div>{item.name}</div>
          </button>
        {:else}
          <Tree_1 folder={item} parent={getPath(item)} depth={depth + 1} bind:focusedFile />
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

  [data-container] {
    --uno: transition-background-color duration-100;
  }

  [data-container]:has(:global(> button:first-child:hover)) {
    --uno: rounded-r-sm bg-neutral-8/10;
  }
</style>
