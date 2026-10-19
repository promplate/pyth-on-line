<script lang="ts">
  import type { Folder } from "$lib/utils/list2tree";

  import Tree from "./Tree.svelte";
  import { unflatten } from "$lib/utils/list2tree";
  import { untrack } from "svelte";

  // File updates must not overwrite a selection the user has already made.
  let { files = [], focusedFile = $bindable(untrack(() => files[0] ?? null)), title = "Files" }: { files?: string[]; focusedFile?: string | null; title?: string } = $props();

  const root: Folder = $derived({ name: "", children: unflatten(files), type: "folder" });
</script>

<div class="relative h-full select-none gap-1 overflow-y-scroll">
  <h2 class="sticky top-0 bg-gradient-(from-neutral-9/0 to-neutral-9/80 to-t) pb-1 pl-2 pt-2 text-sm font-bold tracking-wide">{title}</h2>
  <div class="pb-1.5">
    <Tree folder={root} bind:focusedFile />
  </div>
</div>
