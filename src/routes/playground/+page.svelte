<script lang="ts">
  import files from "../../python";
  import FileContent from "./FileContent.svelte";
  import FileList from "./FileList.svelte";
  import Console from "$lib/components/Console.svelte";
  import { Pane, PaneGroup, PaneResizer } from "paneforge";

  let focusedFile: keyof typeof files = Object.keys(files)[0] as keyof typeof files;
  let container: HTMLElement;
</script>

<div class="h-screen">
  <PaneGroup direction="horizontal">
    <Pane defaultSize={20} minSize={10}>
      <FileList files={Object.keys(files).toSorted()} bind:focusedFile />
    </Pane>
    <PaneResizer class="group">
      <div class="mx-1 h-full w-0.11em bg-white/10 transition group-active:bg-current group-hover:bg-white/30" />
    </PaneResizer>
    <Pane defaultSize={80} minSize={10}>
      <PaneGroup direction="vertical">
        <Pane defaultSize={70} minSize={10}>
          <FileContent content={files[focusedFile]} lang={focusedFile.slice(focusedFile.lastIndexOf(".") + 1)} />
        </Pane>
        <PaneResizer class="group">
          <div class="my-1 h-0.11em w-full bg-white/10 transition group-active:bg-current group-hover:bg-white/30" />
        </PaneResizer>
        <Pane defaultSize={30} minSize={10}>
          <div class="h-full w-full overflow-y-scroll" bind:this={container}>
            <Console class="p-2 text-xs [&>div:hover]:rounded-r-none @2xl:(text-13px line-height-18px) @7xl:text-sm" {container} />
          </div>
        </Pane>
      </PaneGroup>
    </Pane>
  </PaneGroup>
</div>
