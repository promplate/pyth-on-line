<script lang="ts">
  export let files: string[] = [];

  export let focusedFile = files.length ? files![0] : null;

  export let title = "Files";
</script>

<div class="flex flex-col select-none py-2">
  <h2 class="ml-2 text-sm font-bold tracking-wide">{title}</h2>
  {#each files as file}
    <button class="w-full overflow-x-hidden text-ellipsis ws-nowrap rounded-r-sm py-0.5 pl-2 pr-1 text-left text-xs text-neutral-1/95 font-mono hover:bg-neutral-8/50" class:!bg-neutral-8={file === focusedFile} on:click={() => focusedFile = file}>
      {file}
    </button>
  {/each}
</div>
