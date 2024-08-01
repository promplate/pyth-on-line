<script lang="ts">
  import FileContent from "./FileContent.svelte";
  import FileList from "./FileList.svelte";
  import Console from "$lib/components/Console.svelte";
  import SetupWorkspace from "$lib/components/reusable/WorkspaceLifecycle.svelte";
  import { toastMarkdown } from "$lib/utils/toast";
  import { Pane, PaneGroup, PaneResizer } from "paneforge";

  export let sources: Record<string, string> = {};

  let focusedFile: keyof typeof sources = Object.keys(sources)[0] as keyof typeof sources;
  let container: HTMLElement;
</script>

<div class="h-screen">
  <PaneGroup direction="horizontal">
    <Pane defaultSize={20} minSize={10}>
      <FileList files={Object.keys(sources).toSorted()} bind:focusedFile />
    </Pane>
    <PaneResizer class="group">
      <div class="mx-1 h-full w-0.11em bg-white/10 transition group-active:bg-current group-hover:bg-white/30" />
    </PaneResizer>
    <Pane defaultSize={80} minSize={10}>
      <PaneGroup direction="vertical">
        <SetupWorkspace {sources} let:save>
          <Pane defaultSize={70} minSize={10} class="relative">
            <FileContent on:save={({ detail: content }) => {
              const diff = save(focusedFile, content.replaceAll("\r\n", "\n"));
              diff
                ? toastMarkdown(`\`${focusedFile}\` saved\n\n${diff}`)
                : toastMarkdown(`\`${focusedFile}\` is up to date`);
            }} bind:content={sources[focusedFile]} lang={focusedFile.slice(focusedFile.lastIndexOf(".") + 1)} />
          </Pane>
          <PaneResizer class="group">
            <div class="my-1 h-0.11em w-full bg-white/10 transition group-active:bg-current group-hover:bg-white/30" />
          </PaneResizer>
          <Pane defaultSize={30} minSize={10}>
            <div class="h-full w-full overflow-y-scroll" bind:this={container}>
              <Console class="p-2 text-xs [&>div:hover]:rounded-r-none @2xl:(text-13px line-height-18px) @7xl:text-sm" {container} />
            </div>
          </Pane>
        </SetupWorkspace>
      </PaneGroup>
    </Pane>
  </PaneGroup>
</div>
