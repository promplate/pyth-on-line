<script lang="ts">
  import ConsolePrompt from "../ConsolePrompt.svelte";
  import WithTooltip from "../reusable/WithTooltip.svelte";
  import ButtonGroup from "./ButtonGroup.svelte";
  import Copy from "./Copy.svelte";
  import Highlight from "./Highlight.svelte";

  export let text = "";
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
      <WithTooltip tips="再次运行" let:builder>
        <button on:click class="i-mingcute-play-fill" {...builder} use:builder.action />
      </WithTooltip>
    </ButtonGroup>
  </div>
{:else}
  <section class="animate-(fade-out duration-300 both)">
    <ConsolePrompt />
  </section>
{/if}
