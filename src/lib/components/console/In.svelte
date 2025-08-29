<script lang="ts">
  import { createBubbler } from "svelte/legacy";

  const bubble = createBubbler();
  import ConsolePrompt from "../ConsolePrompt.svelte";
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import ButtonGroup from "./ButtonGroup.svelte";
  import Copy from "./Copy.svelte";
  import Highlight from "./Highlight.svelte";

  interface Props {
    text?: string;
  }

  const { text = "" }: Props = $props();
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
        {#snippet children({ builder })}
          <button onclick={bubble("click")} class="i-mingcute-play-fill" {...builder} use:builder.action></button>
        {/snippet}
      </WithTooltip>
    </ButtonGroup>
  </div>
{:else}
  <section class="animate-(fade-out duration-300 both)">
    <ConsolePrompt />
  </section>
{/if}
