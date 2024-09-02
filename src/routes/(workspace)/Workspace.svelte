<script lang="ts">
  import FileContent from "./FileContent.svelte";
  import FileList from "./FileList.svelte";
  import { registerCommandGroup } from "$lib/components/command/helper";
  import Console from "$lib/components/Console.svelte";
  import SetupWorkspace from "$lib/components/reusable/WorkspaceLifecycle.svelte";
  import { toastMarkdown } from "$lib/utils/toast";
  import { Pane, PaneGroup, PaneResizer } from "paneforge";

  export let sources: Record<string, string> = {};

  function getDefaultFile() {
    return Object.keys(sources).find(name => name.toUpperCase().startsWith("README")) ?? Object.keys(sources)[0];
  }

  let focusedFile: keyof typeof sources = getDefaultFile();
  let container: HTMLElement;

  registerCommandGroup("工作区", Object.keys(sources).map(name => ({
    text: `打开 ${name}`,
    handler() {
      focusedFile = name;
    },
  })));
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
              save(focusedFile, content.replaceAll("\r\n", "\n"));
              toastMarkdown(`\`${focusedFile}\` 已保存`);
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
