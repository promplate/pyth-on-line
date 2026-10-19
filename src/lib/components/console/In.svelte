<script lang="ts">
  import ConsolePrompt from "../ConsolePrompt.svelte";
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import ButtonGroup from "./ButtonGroup.svelte";
  import Copy from "./Copy.svelte";
  import Highlight from "./Highlight.svelte";
  import { fromAction } from "svelte/attachments";

  const { text = "", onclick }: { text?: string; onclick?: (event: MouseEvent) => void } = $props();
</script>

{#if text !== ""}
  <div class="group relative flex flex-row">
    <div class="flex flex-col gap-0.2em">
      <ConsolePrompt />
      {#each Array.from({ length: text.match(/\n/g)?.length ?? 0 }) as _}
        <ConsolePrompt prompt="..." />
      {/each}
    </div>
    <Highlight {text}></Highlight>
    <ButtonGroup>
      <Copy {text} />
      <WithTooltip tips="Run">
        {#snippet children(builder)}
          <button class="i-mingcute-play-fill" {...builder} {onclick} {@attach fromAction((node: HTMLElement) => builder.action(node), () => undefined)} />
        {/snippet}
      </WithTooltip>
    </ButtonGroup>
  </div>
{:else}
  <section class="animate-(fade-out duration-300 both)">
    <ConsolePrompt />
  </section>
{/if}
