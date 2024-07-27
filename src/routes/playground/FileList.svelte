<script lang="ts">
  import Tree from "./Tree.svelte";
  import { type Folder, unflatten } from "$lib/utils/list2tree";

  export let files: string[] = [];

  export let focusedFile = files.length ? files![0] : null;

  export let title = "Files";

  $: root = { name: "", children: unflatten(files), type: "folder" } as Folder;
</script>

<div class="flex flex-col select-none gap-1 py-2">
  <h2 class="ml-2 text-sm font-bold tracking-wide">{title}</h2>
  <Tree folder={root} bind:focusedFile />
</div>
