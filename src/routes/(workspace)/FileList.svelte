<script lang="ts">
  import Tree from "./Tree.svelte";
  import { type Folder, unflatten } from "$lib/utils/list2tree";

  export let files: string[] = [];

  export let focusedFile = files.length ? files![0] : null;

  export let title = "Files";

  $: root = { name: "", children: unflatten(files), type: "folder" } as Folder;
</script>

<div class="relative h-full select-none gap-1 overflow-y-scroll">
  <h2 class="sticky top-0 bg-gradient-(from-neutral-9/0 to-neutral-9/80 to-t) pb-1 pl-2 pt-2 text-sm font-bold tracking-wide">{title}</h2>
  <div class="pb-1.5">
    <Tree folder={root} bind:focusedFile />
  </div>
</div>
