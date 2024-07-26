<script lang="ts">
  import Tree from "./Tree.svelte";
  import { unflatten } from "$lib/utils/list2tree";

  export let files: string[] = [];

  export let focusedFile = files.length ? files![0] : null;

  export let title = "Files";

  $: tree = unflatten(files);
</script>

<div class="flex flex-col select-none gap-1 py-2">
  <h2 class="ml-2 text-sm font-bold tracking-wide">{title}</h2>
  <Tree {tree} bind:focusedFile />
</div>
