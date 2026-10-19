<script lang="ts">
  import FileContent from "./FileContent.svelte";
  import FileList from "./FileList.svelte";
  import { registerCommandGroup } from "$lib/components/command/helper";
  import Console from "$lib/components/Console.svelte";
  import SetupWorkspace from "$lib/components/reusable/WorkspaceLifecycle.svelte";
  import { toastMarkdown } from "$lib/utils/toast";
  import { Pane, PaneGroup, PaneResizer } from "paneforge";
  import { untrack } from "svelte";

  const { sources: initialSources = {} }: { sources?: Record<string, string> } = $props();

  // Each project owns an editable snapshot; same-project reloads must not overwrite local edits.
  const sources = $state(untrack(() => ({ ...initialSources })));

  function getDefaultFile() {
    return Object.keys(sources).find(name => name.toUpperCase().startsWith("README")) ?? Object.keys(sources)[0];
  }

  let focusedFile = $state<string | null>(untrack(() => getDefaultFile() ?? null));
  let container = $state<HTMLElement>();

  registerCommandGroup("Workspace", Object.keys(sources).map(name => ({
    text: `Open ${name}`,
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
        <SetupWorkspace {sources}>
          {#snippet children(workspace, failed)}
            <Pane defaultSize={70} minSize={10} class="relative">
              {#if focusedFile !== null}
                {@const path = focusedFile}
                <FileContent onsave={(content) => {
                  if (!workspace) {
                    toastMarkdown(failed ? "Workspace initialization failed. Changes have not been saved." : "Workspace is still loading. Try saving again once it is ready.", failed ? "error" : "warning");
                    return;
                  }
                  workspace.save(path, content.replaceAll("\r\n", "\n"));
                  toastMarkdown(`\`${path}\` saved`);
                }} bind:content={sources[path]} lang={path.slice(path.lastIndexOf(".") + 1)} />
              {/if}
            </Pane>
            <PaneResizer class="group">
              <div class="my-1 h-0.11em w-full bg-white/10 transition group-active:bg-current group-hover:bg-white/30" />
            </PaneResizer>
            <Pane defaultSize={30} minSize={10}>
              <div class="h-full w-full overflow-y-scroll" bind:this={container}>
                <Console class="p-2 text-xs [&>div:hover]:rounded-r-none @2xl:(text-13px line-height-18px) @7xl:text-sm" {container} />
              </div>
            </Pane>
          {/snippet}
        </SetupWorkspace>
      </PaneGroup>
    </Pane>
  </PaneGroup>
</div>
